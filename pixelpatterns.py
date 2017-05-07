import time
import thread

class PixelFader:
    fading = None
    speed = None

    def __init__(self):
        self.fading = 0
        self.steps = 0.01
        self.speed = 4000

        try:
           thread.start_new_thread( update, (self, 10) )
        except:
           print "Error: unable to start fader"


    def fade(self, colorRGB):
        for color in colorRGB:
            color = int(color * self.fading)
        return colorRGB

    def update(self, delay):

        self.fading = self.fading + self.steps

        if self.fading <= 0 or self.fading >= 1:
            self.steps = -self.steps

        #x = (time.time() * 1000 % self.speed)/self.speed*100
        #self.fading = self.fading/100
        print(self.fading)
