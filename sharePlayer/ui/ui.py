import logging
logger = logging.getLogger("sharePlayer:UI")

import urwid
import random
import string

from .scroll import ScrollBar, Scrollable
from .Chat import ChatMessages
from . import Chat

url = '(c) https://github.com/bannsec/sharePlayer'

banner = """  ___ / /  ___ ________ / _ \/ /__ ___ _____ ____
 (_-</ _ \/ _ `/ __/ -_) ___/ / _ `/ // / -_) __/
 /___/_//_/\_,_/_/  \__/_/  /_/\_,_/\_, /\__/_/   
                                   /___/          {0}""".format(url)

# http://urwid.org/manual/displayattributes.html
palette = [
    ('username', 'light gray', 'dark gray'),
    ('username_bold', 'light green', 'dark gray'),
    ('frame_background', 'white', 'dark gray'),
    ('panels_background', 'white', 'dark gray'), # Match frame for now
    ('menu_item_selected', 'white', 'dark gray'),
    ('menu_item_unselected', 'light gray', 'dark gray'),
    #('panels_background', 'black', 'light gray'),
    ]

MENU_ITEM_QUIT = 'Quit'
MENU_ITEM_CONFIG = 'Configuration'
MENU_ITEM_START_SERVER = 'Start Server'
MENU_ITEM_STOP_SERVER = 'Stop Server'
MENU_ITEM_CONNECT = 'Connect to Server'

# sorted(list(set([x['name'] for x in self._share_player.redis_connection.client_list() if x['cmd'] == 'subscribe'])))

class UI(object):

    def __init__(self, share_player):
        self.popup_input_widget = None
        self._share_player = share_player

        # Draw the base screen
        self.full_draw()

        # Prompt initially for key
        random_key = ''.join(random.choice(string.ascii_letters + string.ascii_lowercase + string.ascii_uppercase) for _ in range(20))
        self.popup_prompt('Set your password. This is a secret that you will share with anyone who you are sharing your viewing experience with. It can be anything, but you want to ensure that it is a password that is not easily guessable. >All< of your traffic will be encrypted using a strong authenticated cipher with this key.\n', callback=self._set_secret_key, linebox_options={'title': 'Shared Key'}, edit_options={'caption': 'key: ', 'edit_text': random_key, 'align': 'center'})
        self.loop.run()

    def _set_secret_key(self, key):
        self._share_player._shared_key = key
        self.redraw()

    def full_draw(self):
        """Fully recreate and re-draw the screen."""

        #self.frame_header = urwid.Padding(urwid.Text(banner, align='left'), align='center')
        self.frame_header = urwid.Text(banner, align='left')
        self.frame_footer = None

        #self.frame_body = urwid.LineBox(urwid.Filler(urwid.Text("test", wrap="space")), title='Main')
        #self.menu_box = urwid.LineBox( urwid.Text('blerg', align='left'), title='Menu')

        #
        # Menu
        #

        self.menu_widgets = [
                urwid.Text(MENU_ITEM_CONFIG, align='left'),
                urwid.Text(MENU_ITEM_START_SERVER, align='left'),
                urwid.Text(MENU_ITEM_STOP_SERVER, align='left'),
                urwid.Text(MENU_ITEM_CONNECT, align='left'),
                urwid.Text(MENU_ITEM_QUIT, align='left'),
                ]
        self.menu_widgets = [urwid.AttrMap(widget, 'menu_item_unselected', 'menu_item_selected') for widget in self.menu_widgets]

        #self.menu_box = urwid.LineBox(urwid.Filler(urwid.Padding(self.menu_widget,width=self.menu_widget.pack()[0]), valign='top'), title="Menu")
        self.menu_box = urwid.LineBox(urwid.ListBox(self.menu_widgets), title='Menu')

        #
        # Chat
        #

        self.chat_box = urwid.LineBox(ChatMessages(), title='Chat')
        self.input_widget = urwid.Edit(caption='> ', multiline=False)
        self.input_box = urwid.LineBox(urwid.Filler(self.input_widget, valign='bottom', height='pack'))

        # Middle box holds chat and input widgets
        self.middle_box = urwid.Pile([self.chat_box, (3, self.input_box)], focus_item=1)

        #
        # Right box
        # 

        self.status_box = urwid.LineBox(urwid.Padding(urwid.Text('Not Connected'), width=30), title='Status')
        self.users_box_list = [
                urwid.Text(MenuConfig.config['User']['username'], align='left'),
                ]
        self.users_box = urwid.LineBox(
                urwid.Padding(urwid.Pile(self.users_box_list), width=30),
                title='Users')
        self.right_box = urwid.Pile([('pack', self.status_box), ('pack', self.users_box)])
        
        self.frame_body = urwid.Columns([(max(x.pack()[0] for x in self.menu_widgets) + 5, self.menu_box), self.middle_box, (40, self.right_box)], dividechars=0, focus_column=1)

        self.frame = urwid.Frame(body=self.frame_body, header=self.frame_header, footer=self.frame_footer, focus_part='body')
        self.loop = urwid.MainLoop(urwid.AttrMap(self.frame, 'frame_background'), palette=palette, unhandled_input=self._unhandled_input)

        # Start watching for user connects
        user_watcher = threading.Thread(target=Chat.monitor_for_users, args=(self,), daemon=True)
        user_watcher.start()


    def redraw(self):
        """Just reassign the base classes to the loop."""
        self.loop.widget = urwid.AttrMap(self.frame, 'frame_background')


    def run(self):
        self.loop.run()

    def _get_focus_list(self):
        """list: General helper to grab the focus list regardless of if the overlay is opened or not."""
        # Is this the overlay prompt?
        if isinstance(self.loop.widget, urwid.container.Overlay):
            return self.loop.widget.get_focus_widgets()
        # Base frame
        else:
            return self.frame.get_focus_widgets()

    def _unhandled_input(self, key):
        focus_list = self._get_focus_list()

        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

        elif key == 'f1':
            import IPython
            IPython.embed()
            self.loop.run()

        elif key == 'f2':
            def cb(inp):
                self.chat_box.base_widget.add(inp)
            self.popup_prompt('Whats up doc?', callback=cb, linebox_options={'title': 'blerg'})

        elif key == 'enter':

            # Selecting a menu item
            if focus_list[-1] in self.menu_widgets:
                self._handle_menu_widget()

            elif hasattr(focus_list[-1], 'base_widget'):
                
                # Was someone typing into the chat box?
                if focus_list[-1].base_widget is self.input_widget:
                    Chat.handle_enter(self)

                # Handle popup input enter
                elif focus_list[-1].base_widget is self.popup_input_widget:
                    self._handle_popup_input_enter()


        elif key == "down":

            # Take care of changing the focus of the menu widgets
            if focus_list[-1] in self.menu_widgets:
                listbox = focus_list[-2].base_widget
                new_pos = listbox.focus_position + 1 if listbox.focus_position < len(listbox.body) - 1 else listbox.focus_position
                listbox.set_focus(new_pos)

        elif key == "up":

            # Take care of changing the focus of the menu widgets
            if focus_list[-1] in self.menu_widgets:
                listbox = focus_list[-2].base_widget
                new_pos = listbox.focus_position - 1 if listbox.focus_position != 0 else 0
                listbox.set_focus(new_pos)

        #else:
        #    print("uncaught: " + key)

    def _handle_menu_widget(self):
        """Someone pressed enter on a menu item."""
        focus_list = self._get_focus_list()

        selection = focus_list[-1].base_widget.get_text()[0]
        
        if selection == MENU_ITEM_QUIT:
            raise urwid.ExitMainLoop()

        elif selection == MENU_ITEM_CONFIG:
            MenuConfig.run_view(self)

        elif selection == MENU_ITEM_START_SERVER:
            MenuServer.start_server(self)

        elif selection == MENU_ITEM_STOP_SERVER:
            MenuServer.stop_server(self)

        elif selection == MENU_ITEM_CONNECT:
            MenuClient.connect(self)
        

    def _handle_popup_input_enter(self):
        """Called when someone hits enter in the popup window."""
        # Grab input text
        text = self.popup_input_widget.get_edit_text()
        self.redraw()
        self.popup_input_callback(text)

            
    def popup_prompt(self, text, callback, text_options=None, edit_options=None, linebox_options=None):
        """Prompt user for some text input.
        
        Args:
            text (str): What text to prompt the user with
            callback (function): Once input has been gotten, return that input to this function. callback(input)
        """
    
        text_options = {} if text_options is None else text_options
        edit_options = {} if edit_options is None else edit_options
        linebox_options = {} if linebox_options is None else linebox_options

        self.popup_input_callback = callback

        # Set some defaults
        if 'align' not in text_options:
            text_options['align'] = 'center'

        popup_prompt = urwid.Padding(urwid.Text(text, **text_options), width='pack')
        self.popup_input_widget = urwid.Edit(multiline=False, **edit_options)
        
        popup = urwid.Pile([('pack', popup_prompt), urwid.BoxAdapter(urwid.Filler(self.popup_input_widget), height=1)], focus_item=1)
        popup = urwid.LineBox(popup, **linebox_options)
        popup = urwid.AttrMap(popup, 'panels_background')
        
        self.loop.widget = urwid.Overlay(
            popup, self.loop.widget,
            align=("relative", 50),
            valign=("relative",  50),
            width=("relative", 40), height='pack')

import threading

from . import Config as MenuConfig
from ..server import Server as MenuServer
from ..server import Client as MenuClient
