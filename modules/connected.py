
class Connected:
    """
    Keep track of who is connected
    """

    def __init__(self):
        self._connected = []

    def setConsole(self,console):
        self._console = console

    def add(self,host):
        self._connected.append(host)
        self._console.draw()

    def remove(self,host):
        try:
            self._connected.remove(host)
            self._console.draw()
        except:
            # Usually this will happen if there is a failed authentication
            pass

    def draw(self,height,width):

        return "Connected: {0}".format(
            ','.join([host for host in self._connected])
        )

