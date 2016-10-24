from sharePlayer.player import BasePlayer
import mplayer

class MPlayer(BasePlayer):
    
    def __init__(self):
        # Instantiate a new player
        self._player = mplayer.Player()

    def loadfile(self,fName):
        self._player.loadfile(fName)

    def play(self):
        """
        Play the video from current position.
        """
        # mplayer really only knows pause, so we figure out the state for it

        # Only unpause if we're paused
        if self.isPaused():
            self._player.pause()
        

    def pause(self):
        # If it's already paused, we're good
        if self.isPaused():
            return True

        # Else, let's pause it
        self._player.pause()
        return True

    def seek(self,pos):
        self._player.time_pos = pos

    def isPaused(self):
        return self._player.paused

    def curTime(self):
        return self._player.time_pos
    


    

