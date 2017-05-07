class pixelFader:
    def __init__(self):
        fade = 100
        speed = 4000

    def fade(self, colorRGB):
        for color in colorRGB:
            color = color*fade
        return colorRGB

    def update(self):
        x = (time.time() * 1000 % 4000)/40
        fade = fade * 100
