
class ConsoleUI:
    
    def __init__(self):
        # List of modules to use
        #self._modules = [] # --> {'module','height','width'}
        self._views = {}
        self._activeView = None

        self.setPrompt("> ")

        self._setConsoleDimensions()        

    def _setConsoleDimensions(self):

        # Grab current console dimensions
        self._height = shutil.get_terminal_size().lines
        self._width = shutil.get_terminal_size().columns
        
        # Always save a spot for the input at the bottom
        self._height -= 1

    def createView(self,viewName):
        """
        Creates a UI view by name. I.e.: "mainMenu"
        """
        self._views[viewName] = []  # --> {'module','height','width'}

    def setActiveView(self,viewName):
        """
        Set which view is currently active
        """
        self._activeView = viewName

    def registerModule(self,module,height=100,width=100):
        """
        Adds a module to the module list for displaying.
        module.draw(height,width) will be called to render
        height and width are percents of the screen
        This will register the module to the current active view
        """
        
        # Sanity check
        if height not in range(0,101) or width not in range(0,101):
            log.error("Module registration failed. Height needs to be a percent int between 0 and 100. Registration attempt was for ({0},{1})".format(height,width))
        
        # Grab the module list for our current view
        modules = self._views[self._activeView]

        # Add it
        modules.append({
            "module": module,
            "height": height,
            "width": width
        })

        # Register itself with the module
        module.setConsole(self)


        
    def draw(self):
        """
        Actually re-draw the screen
        """
        # Double check the size of our console
        self._setConsoleDimensions()

        cls()

        # Check that we have a valid active view
        if self._activeView == None:
            print("Error! No valid active view!")
            return

        modules = self._views[self._activeView]
        
        # TODO: Need to make the height/width calculation here more accurate
        # This will get messed up with multiple modules

        # Keep track of what we've already allocated
        allocatedHeight = 0

        for module in modules:

            allocatedWidth = 0

            # Figure out the base allocations
            baseHeight=int(self._height / 100 * module['height'])
            baseWidth=int(self._width / 100 * module['width'])

            # If we attempted to allocate too much, give the max possible
            if allocatedHeight + baseHeight > self._height:
                baseHeight = self._height - allocatedHeight

            # Update how much we've allocated
            allocatedHeight += baseHeight
            
            # Let's draw a box around them. Need to adjust the hight and width
            height = baseHeight - 2
            width = baseWidth - 4
            
            out = module['module'].draw(
                height=height,
                width=width)
            # Top border
            print("+" + "-"*(baseWidth-2) + "+")

            for line in out.split("\n")[:height]:
                print("| " + line + " " * (baseWidth - len(line) - 3) + "|")

            # Bottom border
            print("+" + "-"*(baseWidth-2) + "+")

            # Adjust for any unused space
            allocatedHeight -= (baseHeight - len(out.split("\n")) - 2)


        ####
        # Always add the prompt at the bottom
        ####
        
        sys.stdout.write(self._prompt)
        sys.stdout.flush()

    def setPrompt(self,prompt):
        self._prompt = prompt

    def input(self):
        """
        Implementing get input call directly in the console. This helps make the look and feel better
        Use setPrompt to set a custom prompt
        """
        # For now, just do this
        return input()


import shutil
import logging
import sys

from sharePlayer.helpers import cls

log = logging.getLogger("ConsoleUI")

