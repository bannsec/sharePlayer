
class Banner:
    """
    Just a silly banner class
    """

    def __init__(self):
        pass

    def setConsole(self,console):
        self._console = console

    def draw(self,height,width):

        # If we're in too small of an area to actually draw, just type
        if height < 4 or width < 49:
            return "sharePlayer"

        else:
            return banner


banner = """  ___ / /  ___ ________ / _ \/ /__ ___ _____ ____
 (_-</ _ \/ _ `/ __/ -_) ___/ / _ `/ // / -_) __/
/___/_//_/\_,_/_/  \__/_/  /_/\_,_/\_, /\__/_/   
                                  /___/          """
