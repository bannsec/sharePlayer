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
        """
        Attempt to seek to the given position.
        Returns the ACTUAL position seek'd to. This is due to needing to be on keyframes
        """
        # See if we're already there
        if abs(self._player.time_pos - pos) < 0.5:
            return self._player.time_pos

        
        # Find the previous frame
        self._player.seek(pos,2)
        self.play()
        self.pause()
        
        # If we're at the correct place now, return
        if abs(self._player.time_pos - pos) < 0.5:
            return self._player.time_pos

        # Got some differences here. Let's find the last keyframe
        oldKeyFrame = self._player.time_pos
        keyFrame = oldKeyFrame
        
        # Find our way back to the previous
        while oldKeyFrame == keyFrame:
            # Remove a second
            pos -= 1
            
            self._player.seek(pos,2)
            self.play()
            self.pause()

            keyFrame = self._player.time_pos

        # Found it. Return it
        return keyFrame
            

        
        

    def isPaused(self):
        return self._player.paused

    def curTime(self):
        return self._player.time_pos
    


    

