#!/usr/bin/env python3

import nacl.hash, nacl.encoding, nacl.secret, nacl.utils
import readline
import asyncio
import logging

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

def send(buf):
    """
    Encrypt and send the buf
    """
    assert type(buf) == bytes
    
    # Build a new nonce
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)

    encrypted = box.encrypt(buf, nonce)
    
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
    client_writer.write("HELLO\n".encode())

    while True:
        data = yield from asyncio.wait_for(client_reader.readline(),timeout=None)
        print("Got {0}".format(data))


def startServer():
    print("Starting server on {0}:{1}".format(SERVER_HOST,SERVER_PORT))
    
    loop = asyncio.get_event_loop()
    f = asyncio.start_server(accept_client, host=SERVER_HOST, port=SERVER_PORT)
    loop.run_until_complete(f)
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

