
class Connected:
    """
    Keep track of who is connected
    """

    def __init__(self,console):
        self._connected = []
        self._console = console

    def add(self,host):
        self._connected.append(host)
        self._console.draw()

    def remove(self,host):
        self._connected.remove(host)
        self._console.draw()

    def draw(self,height,width):

        return "Connected: {0}".format(
            ','.join([host for host in self._connected])
        )

