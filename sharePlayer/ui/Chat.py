
# https://github.com/andrelaszlo/gevent-chat/blob/master/client.py

from urwid import SimpleFocusListWalker, ListBox, Text
import datetime

class ChatMessages(ListBox):
    """ Show the last couple of chat messages as a scrolling list """

    def __init__(self):
        self.walker = SimpleFocusListWalker([])
        super(ChatMessages, self).__init__(self.walker)

    def add(self, message, user):
        now = datetime.datetime.now().strftime("%b %d %Y %H:%M:%S")
        txt = Text([('username', now + ' '), ('username_bold', user), ('username', ' > '), message])
        self.walker.append(txt)
        self.set_focus(len(self.walker)-1)

def handle_enter(ui):
    """This is called when someone presses enter in the chat edit box. Presumably to send a message."""
    global my_chat_history

    # Grab input text
    text = ui.input_widget.get_edit_text()

    # Clear it
    ui.input_widget.set_edit_text("")

    # Record it so we don't duplicate ourselves
    my_chat_history.append(text)
    
    # Add to the chat log
    if text != '':
        ui.chat_box.base_widget.add(text, MenuConfig.config['User']['username'])

        # Send off our message to anyone connected
        if ui._share_player.redis_connection is not None:
            message = {'user': MenuConfig.config['User']['username'], 'message': text}
            ui._share_player.redis_connection.publish('Chat', json.dumps(message))


def do_subscribe(ui):
    """Once we are connected to Redis, this gets called to Chat can setup the pipes to watch for incoming chat messages."""

    def handle_chat_callback(cb):
        # {'type': 'message', 'pattern': None, 'channel': b'Chat', 'data': b'{"user": "Me2", "message": "test2"}'}
        if cb['type'] == 'message' and cb['channel'] == b'Chat':
            message = json.loads(cb['data'])
            user = message['user']
            text = message['message']

            # If this is our own chat comming back to us
            if user == MenuConfig.config['User']['username'] and text in my_chat_history:
                return

            # TODO: Data sanitization?
            ui.chat_box.base_widget.add(text, user)
            ui.loop.draw_screen()


    ui._share_player.redis_pubsub.subscribe(**{'Chat': handle_chat_callback})
    ui._share_player.redis_connection.client_setname(MenuConfig.config['User']['username'])
    t = ui._share_player.redis_pubsub.run_in_thread(sleep_time=0.001, daemon=True)

def monitor_for_users(ui):
    """Poll for new users to keep the logged in users panel up to date."""

    while True:
        rebuild_connected_users(ui)
        sleep(0.5)

def rebuild_connected_users(ui):
    """Update/rebuild the connected users panel."""
    
    users_box_list = []

    # If we're connected to redis, loop up who is here
    if ui._share_player.redis_connection is not None:
        # TODO: Deal with connections with no name
        for name in sorted(list(set([x['name'] for x in ui._share_player.redis_connection.client_list() if x['cmd'] == 'client']))):
            users_box_list.append(urwid.Text(name, align='left'))

    # If we're not connected, it must just be us
    else:
        users_box_list = [
            urwid.Text(MenuConfig.config['User']['username'], align='left'),
        ]

    # If it's the same size list, check the entries
    if len(users_box_list) == len(ui.users_box_list):

        # Check if there's a difference
        for x,y in zip(users_box_list, ui.users_box_list):

            if x.get_text() != y.get_text():
                break
        else:
            # Nothing changed, don't redraw
            #print('nothing changed')
            return

    # Something changed, redraw
    ui.users_box_list = users_box_list
    ui.users_box.base_widget.widget_list = ui.users_box_list
    print("") # This is needed for some reason to wake up the ui to redraw
    ui.loop.draw_screen()

import urwid
from . import Config as MenuConfig
from ..server import Server
import json
import collections
from time import sleep

try:
    my_chat_history
except:
    # Only keep last 5 items of chat history
    my_chat_history = collections.deque(maxlen=5)

