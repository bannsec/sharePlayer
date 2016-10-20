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
import progressbar
import configparser
import appdirs
from time import sleep


from sharePlayer.ui.console import ConsoleUI
from sharePlayer.modules.chat import Chat
from sharePlayer.modules.banner import Banner
from sharePlayer.modules.connected import Connected
from sharePlayer.modules.menu import Menu
from sharePlayer.modules.text import Text


##################
# Initializing UI
#####################
#
# Chat UI
#
console = ConsoleUI()
console.createView("Chat")
console.setActiveView("Chat")

# Basic modules first
chat = Chat()
connected = Connected()
main_menu = Menu()

console.registerModule(Banner(),height=20)
console.registerModule(connected,height=10)
console.registerModule(chat,height=100) # Take up rest of space

#
# Main Menu UI 
#
console.createView("MainMenu")
console.setActiveView("MainMenu")
console.registerModule(Banner(),height=20)
console.registerModule(connected,height=10)

# Basically just take the rest of the space
main_menu.addItem("1","Start Server")
main_menu.addItem("2","Connect To Server")
main_menu.addItem("3","Enter Chat")
main_menu.addItem("4","Send Video")
main_menu.addItem("5","Select Video")
main_menu.addItem("6","Play/Pause")
main_menu.addItem("7","View/Edit Config")
main_menu.addItem("8","Quit")
console.registerModule(main_menu,height=100)

#
# Get Secret
#
text = Text()
text.setText("Set your password. This is a secret that you will share with anyone who you are sharing your viewing experience with. It can be anything, but you want to ensure that it is a password that is not easily guessable. >All< of your traffic will be encrypted using a strong authenticated cipher with this key.")
console.createView("GetPassword")
console.setActiveView("GetPassword")
console.registerModule(Banner(),height=20)
console.registerModule(text,height=100)



SERVER_HOST = "0.0.0.0"
SERVER_PORT = 12345

LIMIT=8*1024*1024 # streams read and write buffer size, might not actually need this anymore...
SENDSIZE=4*1024*1024 # The size of chunks of data to use when sending a file

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

def initConfig():
    """
    Sets up the config global variable
    """
    def sync():
        """
        Adding function to configfile to sync up
        """
        with open(configFile,"w") as f:
            config.write(f)
    
    global config, configFile

    # Figure out where our config should be
    user_config_dir = appdirs.AppDirs("sharePlayer").user_config_dir

    # Make it if needed
    os.makedirs(user_config_dir,exist_ok=True)

    # Find our config file
    configFile = os.path.join(user_config_dir,"config.ini")
    
    config = configparser.ConfigParser()

    # Adding custom sync command
    config.sync = sync

    # If we don't have one, create it
    if not os.path.isfile(configFile):
        
        config['Server'] = {
            'IP': '0.0.0.0',
            'Port': '12345'
        }

        config['Client'] = {
            'IP' : '',
            'Port': ''
        }
        
        config.sync()

    # If we have a file, read it in
    else:
        config.read(configFile)

def configMenu():
    """
    Menu for showing current config and updating it
    """
    global console

    while True:
        console.setPrompt("config> ")

        # We want a dynamic view. For now, we'll just keep rebuilding it
        if console.hasView("ConfigMenu"):
            console.deleteView("ConfigMenu")
    
        console.createView("ConfigMenu")
        console.setActiveView("ConfigMenu")
        console.registerModule(Banner(),height=20)
        console.registerModule(connected,height=10)

        config_menu = Menu()
    
        config_menu.addItem("1","Default Server IP: {0}".format(config['Server']['IP']))
        config_menu.addItem("2","Default Server Port: {0}".format(config['Server']['Port']))
        config_menu.addItem("3","Default Connect Host: {0}".format(config['Client']['IP']))
        config_menu.addItem("4","Default Connect Port: {0}".format(config['Client']['Port']))
        config_menu.addItem("5","Back")
        console.registerModule(config_menu,height=100)

        console.draw()
        
        # Try to grab an input
        try:
            inp = int(console.input())
        except:
            continue

        if inp == 1:
            new_default = input("New Server IP Default: ")
            config['Server']['IP'] = new_default
            config.sync()
    
        elif inp == 2:
            new_default = input("New Server Port Default: ")
            config['Server']['Port'] = new_default
            config.sync()

        elif inp == 3:
            new_default = input("New Connect Host Default: ")
            config['Client']['IP'] = new_default
            config.sync()

        elif inp == 4:
            new_default = input("New Connect Port Default: ")
            config['Client']['Port'] = new_default
            config.sync()

        elif inp == 5:
            return


def preChecks():
    # Make sure mplayer is installed and in a PATH
    if shutil.which("mplayer") == None:
        log.error("mplayer is not found!")

def setupCrypto():
    global key, box
    global console
    
    console.setActiveView("GetPassword")
    console.setPrompt("Password: ")
    console.draw()
    password = console.input()
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

    return box.encrypt(buf, nonce)
    
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
        host,port = client_writer.get_extra_info('peername')
        client_writer.close()
        # Sending Faux Message to our Queue
        recvQueue.put(encrypt(dill.dumps({
            'type': 'disconnected',
            'host': host,
            'port': port,
            'success': True})))

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

    try:
        # See if we get the right response, timing out
        size = yield from asyncio.wait_for(client_reader.readexactly(4),timeout=2)

    except:
        # The client can choose to fail if it cannot decrypt. This probably
        # happened if we hit here
        host,port = client_writer.get_extra_info('peername')
        # Sending Faux Message to our Queue
        recvQueue.put(encrypt(dill.dumps({
            'type': 'connected',
            'host': host,
            'port': port,
            'success': False})))
        return

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
            data = yield from asyncio.wait_for(client_reader.readexactly(size),timeout=None)
            recvQueue.put(data)

        except concurrent.futures._base.TimeoutError:
            pass

        except asyncio.streams.IncompleteReadError:
            # Assuming the client disconnected here
            return

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
    SERVER_HOST = config['Server']['IP']
    SERVER_PORT = int(config['Server']['Port'])
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

        # Sending Faux Message to our Queue
        recvQueue.put(encrypt(dill.dumps({
            'type': 'disconnected',
            'host': host,
            'port': port,
            'success': True})))

        if len(clients) == 0:
            log.info("clients is empty, stopping loop.")
            loop = asyncio.get_event_loop()
            loop.stop()

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

    # Assume success for now
    host,port = client_writer.get_extra_info('peername')
    # Sending Faux Message to our Queue
    recvQueue.put(encrypt(dill.dumps({
        'type': 'connected',
        'host': host,
        'port': port,
        'success': True})))
    
    while True:
        # Try to read data
        try:
            size = yield from asyncio.wait_for(client_reader.readexactly(4),timeout=0.2)
            size = struct.unpack("<I",size)[0]
            data = yield from asyncio.wait_for(client_reader.readexactly(size),timeout=None)
            recvQueue.put(data)
        except concurrent.futures._base.TimeoutError:
            pass

        except asyncio.streams.IncompleteReadError:
            # Assuming this means disconnect
            return

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


def doChat():
    global console
    console.setActiveView("Chat")

    # We're in the chat, let's set a custom prompt
    console.setPrompt("Chat> ")

    console.draw()

    while True:

        try:
            msg = console.input()
            
            if msg != "":
                
                # Check for control commands
                
                if msg.lower() == "/pause":
                    playPause()
                    console.draw()
                    continue

                if msg.lower() == "/video":
                    selectVideo()
                    console.draw()
                    continue

                if msg.lower() == "/quit":
                    return

                # Add it to our own chat
                chat.addMessage(msg)

                # Send it off to our connected peers
                msg = {
                    'type': 'chat',
                    'msg': msg
                }
                sendQueue.put(dill.dumps(msg))

        except Exception as e:
            print(str(e))
            return

def sendFile(fileName):
    # Path of file to send
    filePath = os.path.abspath(os.path.join(VIDEODIR,fileName))

    # NOTE: Disabling traversal check for now. This should be implemented in
    # the media manager
    # No traversal please...
    #if not filePath.startswith(VIDEODIR):
    #    log.error("You're trying to send something that isn't in your Video directory. Bailing.")
    #    return

    # Figure out the file size
    fileSize = os.path.getsize(filePath)

    # Progress bar to monitor progress
    bar = progressbar.ProgressBar(widgets=[
        ' [', progressbar.Percentage(), '] ',
        progressbar.Bar(),
        ' (', progressbar.ETA(), ') ',
    ],max_value=fileSize)

    with open(filePath,"rb") as f:
        data = f.read(SENDSIZE) # 4MB at a time
        totalRead = len(data)
        
        # So long as we're reading data, send it
        while data != b"":
            bar.update(totalRead)

            # TODO: Rework this "protocol". Right now, it's just going to write files, because... #YOLO
            sendQueue.put(dill.dumps({
                'type': 'fileTransfer',
                'fileName': fileName,
                'data': data
            }))

            data = f.read(SENDSIZE)
            totalRead += len(data)
        
    bar.finish()


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
            #chatMsgs.insert(0,">>> " + msg['msg'])
            chat.addMessage(">>> " + msg['msg'])

        elif msg['type'].lower() == 'connected':
            log.info("Connection {2} from {0}:{1}".format(msg['host'],msg['port'],"success" if msg['success'] else "fail"))
            connected.add(msg['host'])

        elif msg['type'].lower() == 'disconnected':
            log.info("Disconnection {2} from {0}:{1}".format(msg['host'],msg['port'],"success" if msg['success'] else "fail"))
            connected.remove(msg['host'])

        elif msg['type'].lower() == 'load':
            # Loading only the base name for now
            fileName = os.path.basename(msg['fileName'])
            video.loadfile(os.path.join(VIDEODIR,fileName))


        elif msg['type'].lower() == 'pause':
            video.pause()

        elif msg['type'].lower() == "filetransfer":
            # TODO: Opening and closing the file this many times is VERY inefficient
            # TODO: Check if user wants to accept the file
            # TODO: This needs to go into the media manager for better
            # handling... For now, we'll truncate the video name
            fileName = os.path.basename(msg['fileName'])
            # Sanity check
            filePath = os.path.abspath(os.path.join(VIDEODIR,fileName))
            if not filePath.startswith(VIDEODIR):
                log.error("Someone attempted to write to a file outside of your Video directory! They are not your friend. :-(\n\t{0}".format(filePath))
                continue

            # TODO: Assumption we'll always append. Handle initial write better
            with open(filePath,"ab") as f:
                f.write(msg['data'])

        elif msg['type'].lower() == 'time_pos':
            video.time_pos = msg['pos']

        recvQueue.task_done()


def selectVideo(fileName=None):
    global video

    if fileName == None:
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

    # If we just pased it, sync everyone together
    if video.paused:
        sendQueue.put(dill.dumps({
            'type': 'time_pos',
            'pos': video.time_pos
        }))
        video.time_pos = video.time_pos



def menu():
    
    while True:
        # Need to set them here due to returning from functions
        console.setActiveView("MainMenu")
        console.setPrompt("menu> ")
        console.draw()

        try:
            selection = int(console.input())
        except:
            continue

        if selection == 1:
            t = threading.Thread(target=startServer)
            t.daemon = True
            t.start()

        elif selection == 2:
            server = input("Server Host (default: {0})>".format(config['Client']['IP'])) or config['Client']['IP']
            port = input("Server port (default: {0})> ".format(config['Client']['Port'])) or config['Client']['Port']
            t = threading.Thread(target=connectClient,args=(server,int(port)))
            t.daemon = True
            t.start()
        
        elif selection == 3:
            doChat()

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
            configMenu()

        elif selection == 8:
            print("Exiting, bye!")
            exit(0)

def videoMonitor():
    """
    Watches for changes in the video's state. I.e.: if you paused
    Not really using this for now... Kinda hard to implement correctly
    """
    state = video.paused
    state = video.paused
    
    while True:

        newState = video.paused
        
        if newState != state:
            state = newState

        sleep(0.2)


def main():
    # Pre Checks
    preChecks()

    # Setup config
    initConfig()
    
    # Brief pause since mplayer is spitting out ugly errors
    sleep(1)

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


