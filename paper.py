#!/usr/bin/env python

# Author: NicoCrow
# Date: Jun 9th, 2024
# Version: 0.01

# e-paper 2.13'
# 250 × 122px

# based on: https://peppe8o.com/epaper-eink-raspberry-pi/

import sys, os, time, traceback, subprocess, struct, smbus
picdir = "/home/pi/e-Paper/RaspberryPi_JetsonNano/python/pic"
libdir = "/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib" # Set according to your git download
if os.path.exists(libdir): sys.path.append(libdir)
from waveshare_epd import epd2in13_V2
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import RPi.GPIO as GPIO

black = 0
white = 1

def readVoltage(bus):
    "This function returns as float the voltage from the Raspi UPS Hat via the provided SMBus object"
    address = 0x36
    read = bus.read_word_data(address, 0X02)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0]
    voltage = swapped * 1.25 /1000/16
    return voltage

def readCapacity(bus):
    "This function returns as a float the remaining capacity of the battery connected to the Raspi UPS Hat via the provided SMBus object"
    address = 0x36
    read = bus.read_word_data(address, 0X04)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0]
    capacity = swapped/256
    return capacity

def QuickStart(bus):
    address = 0x36
    bus.write_word_data(address, 0x06,0x4000)

def PowerOnReset(bus):
    address = 0x36
    bus.write_word_data(address, 0xfe,0x0054)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(4,GPIO.IN)

bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

PowerOnReset(bus)
QuickStart(bus)

def clear_display(epd):
    global image, draw
    epd.Clear(0xFF)
    image = Image.new('1', (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)
    epd.display(epd.getbuffer(image))

# PI_UPS
def draw_pi_ups(epd):
    draw.rectangle((0, 35, 170, 86), fill = white)

    # Voltage
    draw.text((0, 35), "Voltage:%5.2fV" % readVoltage(bus), font = font16, fill = black)

    # Capacity
    pi_bat_c = readCapacity(bus)
    if pi_bat_c > 100:
        pi_bat_c = 100
    draw.text((0, 52), "Battery:%5i%%" % pi_bat_c, font = font16, fill = black)

    # Adapter
    if (GPIO.input(4) == GPIO.HIGH):
        pi_bat_power = "Power Adapter: Plug In"

    if (GPIO.input(4) == GPIO.LOW):
        pi_bat_power = "Power Adapter Unplug"

    draw.text((0, 68), pi_bat_power, font = font16, fill = black)

def draw_pi_temp(epd):
    draw.rectangle((170, 35, 250, 50), fill = white)
    temp = str(float(subprocess.check_output("vcgencmd measure_temp | grep -o '[0-9]*\.[0-9]*'", shell=True)));
    draw.text((170, 35), 'T=' + temp + '°C', font = font16, fill = black)

# UPS
def draw_ups_level(epd):
    draw.rectangle((145, 0, 165, 16), fill = white)

    try:
        bat_level = subprocess.check_output("upsc ups | grep -o 'battery.charge: [0-9]*' | grep -o '[0-9]*'", shell=True)
        bat = int(bat_level)
        draw.text((145, 0), str(bat) + '%', font = font16, fill = black)

    except:
        print('UPS is not connected')
        draw.text((145, 0), "N/A", font = font16, fill = black)
        bat = 0

    # Draw battery level rect
    # if bat > 0:
    progress = int(bat*2.4) # batterry level in percentage
    draw.rectangle((0, 25, progress, 30), fill = black)
    draw.rectangle((progress, 25, 240, 30), fill = white)
    draw.rectangle([(progress,25),(240,30)],outline = black)

# TIME: HH:MM
def draw_time(epd):
    draw.rectangle((170, 95, 250, 122), fill = white)
    draw.text((170, 95), time.strftime('%H:%M'), font = font24, fill = black)

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

        # Draw battery level text
        draw_ups_level(epd)

        # Draw pi ups params
        draw_pi_ups(epd)

        # Draw pi temp
        draw_pi_temp(epd)

        # Draw time
        draw_time(epd)

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
