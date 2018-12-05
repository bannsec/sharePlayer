
# https://github.com/andrelaszlo/gevent-chat/blob/master/client.py

from urwid import SimpleFocusListWalker, ListBox, Text


class ChatMessages(ListBox):
    """ Show the last couple of chat messages as a scrolling list """

    def __init__(self):
        self.walker = SimpleFocusListWalker([])
        super(ChatMessages, self).__init__(self.walker)

    def add(self, message):
        self.walker.append(Text(message))
        self.set_focus(len(self.walker)-1)

