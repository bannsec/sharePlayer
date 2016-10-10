#!/usr/bin/env python3

import nacl.hash, nacl.encoding, nacl.secret, nacl.utils
import readline
import asyncio
import logging
import random
import struct

logging.basicConfig(level=logging.DEBUG)

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 12345

clients = {} # task -> (reader, writer)
log = logging.getLogger("sharePlayer")

def setupCrypto():
    global key, box

    password = input("Enter password: ")
    key = nacl.hash.sha256(password.encode('ascii'),encoder=nacl.encoding.RawEncoder)
    box = nacl.secret.SecretBox(key)

    print("Encryption Key Set")

def encrypt(buf):
    """
    Encrypt the buf
    """
    assert type(buf) == bytes
    
    # Build a new nonce
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)

    return box.encrypt(buf, nonce,encoder=nacl.encoding.Base64Encoder)
    
def decrypt(buf):
    """
    Decrypt the buf. Returns None if decryption error.
    """
    assert type(buf) in [nacl.utils.EncryptedMessage, bytes]
    
    try:
        return box.decrypt(buf,encoder=nacl.encoding.Base64Encoder)
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
    client_writer.write(encrypt(struct.pack("<I",chal)) + b"\n")

    # See if we get the right response, timing out
    data = yield from asyncio.wait_for(client_reader.readline(),timeout=2)
    print("Response = {0} of type {1}".format(data,type(data)))
    data = decrypt(data.strip())
    resp = struct.unpack("<I",data)[0]

    if resp != chal + 1:
        logging.warn("Invalid response received. Closing connection")
        return

    logging.info("Correct response. Client connected.")

    while True:
        data = yield from asyncio.wait_for(client_reader.readline(),timeout=None)
        print("Got {0}".format(data))


def startServer():
    print("Starting server on {0}:{1}".format(SERVER_HOST,SERVER_PORT))
    
    loop = asyncio.get_event_loop()
    f = asyncio.start_server(accept_client, host=SERVER_HOST, port=SERVER_PORT)
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
    client_reader, client_writer = yield from asyncio.open_connection(host, port)

    log.info("Connected to %s %d", host, port)
    log.debug("Getting challenge")
    
    chal = yield from asyncio.wait_for(client_reader.readline(),timeout=2)
    chal = decrypt(chal.strip())
    
    # Make sure we could even decrypt it
    if chal == None:
        log.warn("Decryption is failing. Are you sure you have the right password?? Bailing.")
        return

    chal = struct.unpack("<I",chal)[0]
    print("Chal received {0}".format(chal))
    
    log.debug("Sending response")
    client_writer.write(encrypt(struct.pack("<I",chal+1)) + b"\n")
    
    
    
    while True:
        command = input("> ") + "\n"
        client_writer.write(command.encode('ascii'))


def connectClient():
    loop = asyncio.get_event_loop()

    server = input("Server IP> ")
    port = int(input("Server port> "))
    
    make_connection(server,port)

    loop.run_forever()

def menu():
    print("Menu")
    print("====")
    print("1) Start Server")
    print("2) Connect To Server")
    print("3) Quit")
    print("")

    while True:
        selection = int(input("> "))

        if selection == 1:
            startServer()

        elif selection == 2:
            connectClient()
        
        elif selection == 3:
            print("Exiting, bye!")
            exit(0)


# Init things
setupCrypto()

menu()

"""
key = nacl.hash.sha256(b"This is my password",encoder=nacl.encoding.RawEncoder)
box = nacl.secret.SecretBox(key)

nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
message = b"Hello!"

encrypted = box.encrypt(message, nonce)

"""

