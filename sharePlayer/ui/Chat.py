
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

