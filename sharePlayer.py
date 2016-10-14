#!/usr/bin/env python3

import nacl.hash, nacl.encoding, nacl.secret, nacl.utils
import readline
import asyncio
import logging
import random
import struct
import threading
import queue
import concurrent
import argparse
import shutil
import os
import mplayer
import subprocess
import base64
import dill

# Custom pyNaCl encoder
from Base85Encoder import Base85Encoder

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 12345

LIMIT=8*1024*1024 # streams read and write buffer size

clients = {} # task -> (reader, writer)
log = logging.getLogger("sharePlayer")

DIR=os.path.dirname(os.path.realpath(__file__))
VIDEODIR = os.path.join(DIR,"Videos")
os.makedirs(VIDEODIR,exist_ok=True)
video = mplayer.Player()

# TODO: This is set up for a single viewing party right now
# Need to update it if we want more than 2 people viewing at the same time
sendQueue = queue.Queue(maxsize=100)
recvQueue = queue.Queue()

# Store the chat messages
chatMsgs = []

def preChecks():
    # Make sure mplayer is installed and in a PATH
    if shutil.which("mplayer") == None:
        log.error("mplayer is not found!")

def setupCrypto():
    global key, box

    password = input("Create Pasword For This Session: ")
    key = nacl.hash.sha256(password.encode('ascii'),encoder=nacl.encoding.RawEncoder)
    box = nacl.secret.SecretBox(key)

    print("Encryption Key Set")

def encrypt(buf):
    """
    Encrypt the buf
    """
    assert type(buf) in [bytes,str]

    # Assuming encoding...
    if type(buf) is str:
        buf = buf.encode('ascii')
    
    # Build a new nonce
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)

    return box.encrypt(buf, nonce)#,encoder=Base85Encoder)
    
def decrypt(buf):
    """
    Decrypt the buf. Returns None if decryption error.
    """
    assert type(buf) in [nacl.utils.EncryptedMessage, bytes]
    
    try:
        return box.decrypt(buf)# ,encoder=Base85Encoder)
    except:
        return None

    
def accept_client(client_reader, client_writer):
    task = asyncio.Task(handle_client(client_reader, client_writer))
    clients[task] = (client_reader, client_writer)

    def client_done(task):
        del clients[task]
        client_writer.close()
        log.info("End Connection")

    log.info("New Connection")
    task.add_done_callback(client_done)



@asyncio.coroutine
def handle_client(client_reader, client_writer):
    logging.debug("Handling Client")

    # Generate the challenge
    chal = random.randint(0,0xffffffff)

    ## Make sure the client knows the password
    logging.debug("Sending Challenge ... {0}".format(chal))
    
    # Encrypt and send the challenge
    chal_enc = encrypt(struct.pack("<I",chal))
    client_writer.write(struct.pack("<I",len(chal_enc)))
    client_writer.write(chal_enc)

    # See if we get the right response, timing out
    size = yield from asyncio.wait_for(client_reader.readexactly(4),timeout=2)
    size = struct.unpack("<I",size)[0]
    data = yield from asyncio.wait_for(client_reader.readexactly(size),timeout=2)
    data = decrypt(data)
    resp = struct.unpack("<I",data)[0]

    if resp != chal + 1:
        logging.warn("Invalid response received. Closing connection")
        return

    logging.info("Correct response. Client connected.")

    host,port = client_writer.get_extra_info('peername')
    # Sending Faux Message to our Queue
    recvQueue.put(encrypt(dill.dumps({
        'type': 'connected',
        'host': host,
        'port': port,
        'success': True})))
    
    while True:
        try:
            # Wait for a size field
            size = yield from asyncio.wait_for(client_reader.readexactly(4),timeout=0.2)
            # If we get a size field, we know we're expecting data so let's get it
            size = struct.unpack("<I",size)[0]
            data = yield from asyncio.wait_for(client_reader.readexactly(size),timeout=0.2)
            recvQueue.put(data)

        except concurrent.futures._base.TimeoutError:
            pass

        try:            
            send = encrypt(sendQueue.get_nowait())
            # First send the size of this message
            client_writer.write(struct.pack("<I",len(send)))
            # Then send the message itself
            client_writer.write(send)
            sendQueue.task_done()
        except queue.Empty:
            pass


def startServer():
    print("Starting server on {0}:{1}".format(SERVER_HOST,SERVER_PORT))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    f = asyncio.start_server(accept_client, host=SERVER_HOST, port=SERVER_PORT,limit=LIMIT)
    loop.run_until_complete(f)
    loop.run_forever()

def make_connection(host, port):

    task = asyncio.Task(handle_client_connection(host, port))

    clients[task] = (host, port)

    def client_done(task):
        del clients[task]
        log.info("Client Task Finished")
        if len(clients) == 0:
            log.info("clients is empty, stopping loop.")
            loop = asyncio.get_event_loop()
            loop.stop()

    log.info("New Client Task")
    task.add_done_callback(client_done)


@asyncio.coroutine
def handle_client_connection(host, port):
    log.info("Connecting to %s %d", host, port)
    client_reader, client_writer = yield from asyncio.open_connection(host, port,limit=LIMIT)

    log.info("Connected to %s %d", host, port)
    log.debug("Getting challenge")
    
    size = yield from asyncio.wait_for(client_reader.readexactly(4),timeout=2)
    size = struct.unpack("<I",size)[0]
    chal = yield from asyncio.wait_for(client_reader.readexactly(size),timeout=2)
    chal = decrypt(chal)
    
    # Make sure we could even decrypt it
    if chal == None:
        log.warn("Decryption is failing. Are you sure you have the right password?? Bailing.")
        return

    chal = struct.unpack("<I",chal)[0]
    
    log.debug("Sending response")
    resp_enc = encrypt(struct.pack("<I",chal+1))
    client_writer.write(struct.pack("<I",len(resp_enc)))
    client_writer.write(resp_enc)
    
    while True:
        # Try to read data
        try:
            size = yield from asyncio.wait_for(client_reader.readexactly(4),timeout=0.2)
            size = struct.unpack("<I",size)[0]
            data = yield from asyncio.wait_for(client_reader.readexactly(size),timeout=0.2)
            recvQueue.put(data)
        except concurrent.futures._base.TimeoutError:
            pass

        try:
            # See if there's something to send
            command = encrypt(sendQueue.get_nowait())
            # First send the length
            client_writer.write(struct.pack("<I",len(command)))
            # Then send the command
            client_writer.write(command)
            sendQueue.task_done()
        except queue.Empty:
            # Not a big deal if there isn't anything to send
            pass
            


def connectClient(server,port):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    make_connection(server,port)
    loop.run_forever()


def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def printChat():
    # TODO: There's a race condition in here both on adding messages and printing. This really needs to be controlled through it's own class
    global chatMsgs

    # Grab the current dimentions
    lines = shutil.get_terminal_size().lines
    columns = shutil.get_terminal_size().columns

    # Clear the screen
    cls()

    # Print the messages we have, padding if need be
    msgs = chatMsgs[:lines-3] if len(chatMsgs) > lines-3 else (['']*(lines - len(chatMsgs) - 3) + chatMsgs)

    for msg in msgs[::-1]:
        print(msg)
    

def chat():
    global chatMsgs

    while True:
        printChat()

        try:
            msg = input("Chat> ")
            if msg != "":

                # Add it to our own chat
                chatMsgs.insert(0,msg)

                # Send it off to our connected peers
                msg = {
                    'type': 'chat',
                    'msg': msg
                }
                sendQueue.put(dill.dumps(msg))

        except:
            print("")
            return

def sendFile(fileName):
    # Path of file to send
    filePath = os.path.abspath(os.path.join(VIDEODIR,fileName))

    # No traversal please...
    if not filePath.startswith(VIDEODIR):
        log.error("You're trying to send something that isn't in your Video directory. Bailing.")
        return

    with open(filePath,"rb") as f:
        data = f.read(4*1024*1024) # 4MB at a time
        
        # So long as we're reading data, send it
        while data != b"":

            # TODO: Rework this "protocol". Right now, it's just going to write files, because... #YOLO
            sendQueue.put(dill.dumps({
                'type': 'fileTransfer',
                'fileName': fileName,
                'data': data.decode('iso-8859-1') # remember to decode after we get it!
            }))


def manageRecvQueue():

    # TODO: Change msg['type'] into int enum that will take up less space on the network
    global chatMsgs

    while True:
        msg = recvQueue.get()
        msg = decrypt(msg)
        msg = dill.loads(msg)

        # Figure out what to do with this message

        if msg['type'].lower() == 'chat':
            subprocess.check_output(["mplayer",os.path.join(DIR,"notifications","just-like-that.mp3")],stderr=subprocess.STDOUT)
            chatMsgs.insert(0,">>> " + msg['msg'])
            printChat()

        elif msg['type'].lower() == 'connected':
            log.info("Connection {2} from {0}:{1}".format(msg['host'],msg['port'],"success" if msg['success'] else "fail"))

        elif msg['type'].lower() == 'load':
            video.loadfile(os.path.join(VIDEODIR,msg['fileName']))

        elif msg['type'].lower() == 'pause':
            video.pause()

        elif msg['type'].lower() == "filetransfer":
            # TODO: Opening and closing the file this many times is VERY inefficient
            # TODO: Check if user wants to accept the file

            # Sanity check
            filePath = os.path.abspath(os.path.join(VIDEODIR,msg['fileName']))
            if not filePath.startswith(VIDEODIR):
                log.error("Someone attempted to write to a file outside of your Video directory! They are not your friend. :-(\n\t{0}".format(filePath))
                continue

            # TODO: Assumption we'll always append. Handle initial write better
            with open(filePath,"ab") as f:
                f.write(msg['data'])

        recvQueue.task_done()


def selectVideo():
    global video

    fileName = input("Video Name> ")
    video.loadfile(os.path.join(VIDEODIR,fileName))
    
    sendQueue.put(dill.dumps({
        'type': 'load',
        'fileName': fileName
    }))


def playPause():
    global video

    video.pause()

    sendQueue.put(dill.dumps({
        'type': 'pause'
        }))

    if video.paused:
        #video.pause()
        pass

    # Sync'up location after pausing...
    else:
        #video.pause()
        pass


def menu():
    print("Menu")
    print("====")
    print("1) Start Server")
    print("2) Connect To Server")
    print("3) Enter Chat mode")
    print("4) Send Video")
    print("5) Select Video")
    print("6) Play/Pause")
    print("7) Quit")
    print("")

    while True:
        try:
            selection = int(input("menu> "))
        except:
            continue

        if selection == 1:
            t = threading.Thread(target=startServer)
            t.daemon = True
            t.start()

        elif selection == 2:
            server = input("Server Host> ")
            port = int(input("Server port> "))
            t = threading.Thread(target=connectClient,args=(server,port))
            t.daemon = True
            t.start()
        
        elif selection == 3:
            chat()

        elif selection == 4:
            fileName = input("Name of file to send> ")
            t = threading.Thread(target=sendFile,args=(fileName,))
            t.daemon = True
            t.start()

        elif selection == 5:
            selectVideo()

        elif selection == 6:
            playPause()

        elif selection == 7:
            print("Exiting, bye!")
            exit(0)


def main():
    # Pre Checks
    preChecks()

    # Init things
    setupCrypto()

    # Spawn off some handlers
    t = threading.Thread(target=manageRecvQueue)
    t.daemon = True
    t.start()

    menu()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="Including debugging output",
                        action="store_true")
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    main()


