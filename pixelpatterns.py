import time

class PixelFader:
    fade = None
    speed = None

    def __init__(self):
        self.fade = 100
        self.speed = 4000

    def fade(self, colorRGB):
        for color in colorRGB:
            color = color * self.fade
        return colorRGB

    def update(self):
        x = (time.time() * 1000 % self.speed)/speed*100
        self.fade = x
