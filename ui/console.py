
class ConsoleUI:
    
    def __init__(self):
        # List of modules to use
        self._modules = [] # --> {'module','height','width'}

        self._setConsoleDimensions()        


    def _setConsoleDimensions(self):

        # Grab current console dimensions
        self._height = shutil.get_terminal_size().lines
        self._width = shutil.get_terminal_size().columns
        
        # Always save a spot for the input at the bottom
        self._height -= 1


    def registerModule(self,module,height=100,width=100):
        """
        Adds a module to the module list for displaying.
        module.draw(height,width) will be called to render
        height and width are percents of the screen
        """
        
        # Sanity check
        if height not in range(0,101) or width not in range(0,101):
            log.error("Module registration failed. Height needs to be a percent int between 0 and 100. Registration attempt was for ({0},{1})".format(height,width))
        
        # Add it
        self._modules.append({
            "module": module,
            "height": height,
            "width": width
        })
        
    def draw(self):
        """
        Actually re-draw the screen
        """
        cls()

        for module in self._modules:
            out = module['module'].draw(
                height=int(self._height / 100 * module['height']),
                width=int(self._width / 100 * module['width']))
            print(out)


import shutil
import logging
from helpers import cls

log = logging.getLogger("ConsoleUI")

