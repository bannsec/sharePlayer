import logging
logger = logging.getLogger("sharePlayer:UI")

import urwid

from .scroll import ScrollBar, Scrollable
from .Chat import ChatMessages

url = '(c) https://github.com/bannsec/sharePlayer'

banner = """  ___ / /  ___ ________ / _ \/ /__ ___ _____ ____
 (_-</ _ \/ _ `/ __/ -_) ___/ / _ `/ // / -_) __/
 /___/_//_/\_,_/_/  \__/_/  /_/\_,_/\_, /\__/_/   
                                   /___/          {0}""".format(url)

# http://urwid.org/manual/displayattributes.html
palette = [
    ('username', 'black', 'light gray'),
    ('frame_background', 'white', 'dark gray'),
    ('panels_background', 'white', 'dark gray'), # Match frame for now
    #('panels_background', 'black', 'light gray'),
    ]

class UI(object):

    def __init__(self):
        self.popup_input_widget = None
        self.full_draw()

    def full_draw(self):
        """Fully recreate and re-draw the screen."""

        #self.frame_header = urwid.Padding(urwid.Text(banner, align='left'), align='center')
        self.frame_header = urwid.Text(banner, align='left')
        self.frame_footer = None

        #self.frame_body = urwid.LineBox(urwid.Filler(urwid.Text("test", wrap="space")), title='Main')
        #self.menu_box = urwid.LineBox( urwid.Text('blerg', align='left'), title='Menu')

        self.menu_widgets = [
                urwid.Text('blerg', align='left'),
                urwid.Text('blerg2', align='left'),
                ]
        self.menu_widgets = [urwid.AttrMap(widget, 'username', 'panels_background') for widget in self.menu_widgets]

        #self.menu_box = urwid.LineBox(urwid.Filler(urwid.Padding(self.menu_widget,width=self.menu_widget.pack()[0]), valign='top'), title="Menu")
        self.menu_box = urwid.LineBox(urwid.ListBox(self.menu_widgets), title='Menu')

        self.chat_box = urwid.LineBox(ChatMessages(), title='Chat')
        self.input_widget = urwid.Edit(caption='> ', multiline=False)

        self.input_box = urwid.LineBox(urwid.Filler(self.input_widget, valign='bottom', height='pack'))

        self.middle_box = urwid.Pile([self.chat_box, (3, self.input_box)], focus_item=1)

        # The far right box, containing whose logged in, and other status sub-boxes
        self.right_box = urwid.LineBox(
                urwid.AttrMap(
                    urwid.Filler(
                        urwid.Padding(
                            urwid.Text('rightbox', align='left'),
                            width='pack'),
                        valign='top'),
                    'panels_background'),
                title="Right")
        
        self.frame_body = urwid.Columns([(self.menu_widgets[0].pack()[0] + 5, self.menu_box), self.middle_box, (40, self.right_box)], dividechars=0, focus_column=1)

        self.frame = urwid.Frame(body=self.frame_body, header=self.frame_header, footer=self.frame_footer, focus_part='body')
        self.loop = urwid.MainLoop(urwid.AttrMap(self.frame, 'frame_background'), palette=palette, unhandled_input=self._unhandled_input)
        self.loop.run()

    def redraw(self):
        """Just reassign the base classes to the loop."""
        self.loop.widget = urwid.AttrMap(self.frame, 'frame_background')


    def run(self):
        self.loop.run()

    def _unhandled_input(self, key):
        # Is this the overlay prompt?
        if isinstance(self.loop.widget, urwid.container.Overlay):
            focus_list = self.loop.widget.get_focus_widgets()
        # Base frame
        else:
            focus_list = self.frame.get_focus_widgets()

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

            if isinstance(focus_list[-1], urwid.graphics.LineBox):
                
                # Was someone typing into the chat box?
                if focus_list[-1].base_widget is self.input_widget:
                    self._handle_chat_enter()

            elif hasattr(focus_list[-1],'base_widget') and focus_list[-1].base_widget is self.popup_input_widget:
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

        else:
            print("uncaught: " + key)

    def _handle_chat_enter(self):
        """This is called when someone presses enter in the chat edit box. Presumably to send a message."""

        # Grab input text
        text = self.input_widget.get_edit_text()

        # Clear it
        self.input_widget.set_edit_text("")
        
        # Add to the chat log
        if text != '':
            self.chat_box.base_widget.add(text)

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

        #popup = urwid.LineBox(urwid.Filler(urwid.Padding(urwid.Text(text))), title=title)
        popup_prompt = urwid.Filler(urwid.Padding(urwid.Text(text, **text_options)))
        
        self.popup_input_widget = urwid.Edit(multiline=False, **edit_options)
        
        popup = urwid.Pile([popup_prompt, urwid.Filler(self.popup_input_widget)], focus_item=1)
        popup = urwid.LineBox(popup, **linebox_options)
        popup = urwid.AttrMap(popup, 'panels_background')

        self.loop.widget = urwid.Overlay(
            popup, self.loop.widget,
            align=("relative", 50),
            valign=("relative",  50),
            width=("relative", 40), height=6) 
