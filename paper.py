# Author: NicoCrow
# Date: Jun 9th, 2024
# Version: 0.01

# e-paper 2.13'
# 250 × 122px

# based on: https://peppe8o.com/epaper-eink-raspberry-pi/

import sys, os, time, traceback, subprocess
picdir = "/home/pi/e-Paper/RaspberryPi_JetsonNano/python/pic"
libdir = "/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib" # Set according to your git download
if os.path.exists(libdir): sys.path.append(libdir)
from waveshare_epd import epd2in13_V2
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

black = 0
white = 1

def clear_display(epd):
    global image, draw
    epd.Clear(0xFF)
    image = Image.new('1', (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)
    epd.display(epd.getbuffer(image))

try:
    epd = epd2in13_V2.EPD()
    epd.init(epd.FULL_UPDATE)
    # epd.Clear(0xFF)

    font16 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 16)
    font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)

# Draw partial Updates
    clear_display(epd)
    draw.text((0, 0), 'Nova 625 AVR UPS:', font = font16, fill = black)
    epd.displayPartBaseImage(epd.getbuffer(image))
    epd.init(epd.PART_UPDATE)

    start_time=time.time()
    elapsed = time.time()-start_time
    while (time.time()-start_time) <= 1000:
        elapsed=time.time()-start_time
        bat = int(subprocess.check_output("upsc ups | grep -o 'battery.charge: [0-9]*' | grep -o '[0-9]*'", shell=True))
        print(bat)

        # Draw battery level text
        draw.rectangle((145, 0, 165, 16), fill = white)
        draw.text((145, 0), str(bat), font = font16, fill = black)
        draw.text((165, 0), '%', font = font16, fill = black)

        # Draw battery level rect
        progress = int(bat*2.4) # batterry level in percentage
        draw.rectangle((0, 25, progress, 30), fill = black)
        draw.rectangle((progress, 25, 240, 30), fill = white)
        draw.rectangle([(progress,25),(240,30)],outline = black)

        # Draw time
        draw.rectangle((120, 80, 220, 105), fill = white)
        draw.text((120, 80), time.strftime('%H:%M'), font = font24, fill = black)
        epd.displayPartial(epd.getbuffer(image))
        time.sleep(10)
    epd.init(epd.FULL_UPDATE)
    time.sleep(2)

# Tests finished
    clear_display(epd)
    draw.text((0, 0), 'Tests finished', font = font16, fill = 0)
    draw.text((0, 16), 'Visit peppe8o.com for more tutorials', font = font16, fill = 0)
    epd.display(epd.getbuffer(image))
    time.sleep(5)

    clear_display(epd)
    print("Goto Sleep...")
    epd.sleep()

except IOError as e:
    print(e)

except KeyboardInterrupt:
    print("ctrl + c:")
    epd2in13_V2.epdconfig.module_exit()
    exit()
