from sharePlayer.player import BasePlayer
import pychromecast
import sys
import os
from RangeHTTPServer import RangeRequestHandler


# Don't output those messages
class QuietHandler(RangeRequestHandler):
    def log_message(self, format, *args):
        return

class ChromeCast(BasePlayer):
    
    def __init__(self):
        # No cast at first
        self._cast = None

    def selectCast(self):
        """
        Walk the user through selection of a chromecast
        """
        
        sys.stdout.write("Searching for available chromecasts ... ")
        sys.stdout.flush()
        
        #casts = [cast.device.friendly_name for cast in pychromecast.get_chromecasts()]
        casts = pychromecast.get_chromecasts()
        
        print("[ Done ]")
        
        print("Select from one of the following: {0}".format(', '.join([cast.device.friendly_name for cast in casts])))
        castName = input("Cast Name> ")
        
        self._cast = [cast for cast in casts if cast.device.friendly_name == castName][0]

        print("Set!")


    def _httpServer(self,directory):
        """
        Starts up an http server in the given directory
        """
        # TODO: There's gotta be a better way to do this...
        os.chdir(directory)
        http.server.test(HandlerClass=QuietHandler)


    def loadfile(self,fName):
        # Make sure we have a cast selected
        if self._cast == None:
            log.error("Must have a ChromeCast selected before we can load a video!")
            return

        # Make sure we're dealing w/ absolute path
        fName = os.path.abspath(fName)

        # Start up the webserver for it
        # TODO: This will likely only work right the first time around. Need to re-work this so that you can load a second video after
        t = threading.Thread(target=self._httpServer,args=(os.path.dirname(fName),))
        t.daemon = True
        t.start()

        # Our IP
        # TODO: Not sure this works everywhere...
        ip = self._cast.socket_client.socket.getsockname()[0]
        
        # Point our chromecast to us
        self._cast.media_controller.play_media('http://{1}:8000/{0}'.format(os.path.basename(fName),ip), 'video/mp4;',autoplay=False)


    def play(self):
        self._cast.media_controller.play()
        

    def pause(self):
        self._cast.media_controller.pause()


    def seek(self,pos):
        assert type(pos) in [int, float]

        # Let it load up
        self._cast.media_controller.seek(pos)
        
        # Pause it immediately
        self.pause()
        
        # ChromeCast can seek in between keyframes. No need to check which frame we're at
        return pos


    def isPaused(self):
        return self._cast.media_controller.is_paused


    def curTime(self):
        return self._cast.media_controller.status.current_time

    def stop(self):
        self._cast.media_controller.stop()
    

    
import os
import RangeHTTPServer
import http.server
import threading
import logging
from time import sleep

log = logging.getLogger("ChromeCast")

