class Chat:
    """
    Implements a chat module
    """
    
    def __init__(self):
        # Store the chat messages
        self._chatMsgs = []
        
        # Input queue. We want to be thread safe!
        self._msgInQueue = queue.Queue()

        # Start our message ingest monitor
        t = threading.Thread(target=self._monitorMsgIn)
        t.daemon = True
        t.start()
        
    def setConsole(self,console):
        self._console = console

    def _monitorMsgIn(self):
        """
        This will be started as a thread to monitor the msg in queue and add messages as they arrive
        """
        while True:
            self._chatMsgs.insert(0,self._msgInQueue.get())
            # Ask it to redraw for us
            self._console.draw()


    def draw(self,height,width):
        """
        Returns a string depiction of the chat
        """
        # Print the messages we have, padding if need be
        msgs = self._chatMsgs[:height] if len(self._chatMsgs) > height  else (['']*(height - len(self._chatMsgs)) + self._chatMsgs)

        return '\n'.join([msg for msg in msgs[::-1]])
        """
        for msg in msgs[::-1]:
            print(msg)

        return '\n'.join([msg for msg in self._chatMsgs])
        """


    def addMessage(self,message):
        assert type(message) is str
        
        # Add it to our ingest queue
        self._msgInQueue.put(message)


import queue
import threading

