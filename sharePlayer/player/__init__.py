"""
Base sharePlayer.player class

The idea is to implement base functionality in a standard way across different players. Thus allowing any of them to be used.
"""

class BasePlayer:
    
    def __init__(self):
        pass

    def play(self):
        # Strictly play, don't pause
        print("Play isn't implemented yet")

    def pause(self):
        # Strictly pause, don't play
        print("Pause isnt' implemented yet")

    def seek(self,pos):
        print("Seek isn't implemented yet")
    
    def loadfile(self,fName):
        print("Load file isn't implemented yet")

    def isPaused(self):
        print("isPaused isn't implemented yet")
        return None

    def curTime(self):
        print("curTime isn't implemented yet")
        return None
    

