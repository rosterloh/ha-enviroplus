import os
import colorsys
import ST7735
from PIL import Image, ImageDraw, ImageFont

_top_pos = 25

class Display():
    def __init__(self):

        self.disp = ST7735.ST7735(
            port=0,
            cs=ST7735.BG_SPI_CS_FRONT,  # BG_SPI_CSB_BACK or BG_SPI_CS_FRONT
            dc=9,
            backlight=12,
            rotation=270,
            spi_speed_hz=16 * 1000 * 1000
        )
        self.disp.begin()
        self.img = Image.new('RGB', (self.disp.width, self.disp.height), color=(0, 0, 0))
        self.draw = ImageDraw.Draw(self.img)
        path = os.path.dirname(os.path.realpath(__file__))
        self.font = ImageFont.truetype(path + "/fonts/Asap/Asap-Bold.ttf", 20)
        self.values = [1] * self.disp.width

    def display_text(self, variable, data, unit):
        # Maintain length of list
        self.values = self.values[1:] + [data]
        # Scale the values for the variable between 0 and 1
        colours = [(v - min(self.values) + 1) / (max(self.values)
                   - min(self.values) + 1) for v in self.values]
        self.message = "{}: {:.1f} {}".format(variable[:4], data, unit)
        self.draw.rectangle((0, 0, self.disp.width, self.disp.height), (255, 255, 255))
        for i in range(len(colours)):
            # Convert the values to colours from red to blue
            colour = (1.0 - colours[i]) * 0.6
            r, g, b = [int(x * 255.0) for x in colorsys.hsv_to_rgb(colour,
                       1.0, 1.0)]
            # Draw a 1-pixel wide rectangle of colour
            self.draw.rectangle((i, _top_pos, i+1, self.disp.height), (r, g, b))
            # Draw a line graph in black
            line_y = self.disp.height - (_top_pos + (colours[i] * (self.disp.height - _top_pos)))\
                     + _top_pos
            self.draw.rectangle((i, line_y, i+1, line_y+1), (0, 0, 0))
        
        # Write the text at the top in black
        self.draw.text((0, 0), self.message, font=self.font, fill=(0, 0, 0))
        self.disp.display(self.img)

if __name__ == '__main__':
    try:
        display = Display()
        display.display_text("temperature", 23.456, "C")
    except KeyboardInterrupt:
        pass