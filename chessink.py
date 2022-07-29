#!/usr/bin/python
# -*- coding:utf-8 -*-

from threading import Lock

import sys
import os
picdir = os.path.join(os.environ["WAVESHARE_DIR"], 'pic')
libdir = os.path.join(os.environ["WAVESHARE_DIR"], 'lib')
sys.path.append(libdir)

from gpiozero import Button

import logging
from waveshare_epd import epd1in54_V2
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

logging.basicConfig(level=logging.DEBUG)

msg = '____'
msgt = msg
msgi = 0
mutex = Lock()
def on_button_a_pressed():
    on_button_pressed('a')
def on_button_b_pressed():
    on_button_pressed('b')
def on_button_c_pressed():
    on_button_pressed('c')

def on_button_pressed(id):
    global mutex
    if mutex.acquire(False):
        global msg
        global msgi
        msg, msgi = process_button(msg, msgi, id)
        time.sleep(0.15) # "pressed" triggers multiple events for more than 0.1s
        mutex.release()

def process_button(msg, msgi, button):
    aux = list(msg)
    if button == 'a':
        if aux[msgi] == '_':
            aux[msgi] = 'a' if msgi % 2 == 0 else '1'
        else:
            aux[msgi] = chr(ord(aux[msgi]) + 1)
    if button == 'b':
        if aux[msgi] == '_':
            aux[msgi] = 'd' if msgi % 2 == 0 else '4'
        else:
            aux[msgi] = chr(ord(aux[msgi]) + 4)
    if button == 'c':
        msgi += 1
    return ''.join(aux), msgi

def changed():
    global msg
    global msgt
    res = (msg != msgt)
    if res:
        msgt = msg
    return res

try:
    logging.info("epd1in54_V2 Demo")
    
    epd = epd1in54_V2.EPD()
    
    logging.info("init and Clear")
    epd.init(0)
    epd.Clear(0xFF)
    
    # partial update
    logging.info("4.show time...")
    font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
    time_image = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
    epd.displayPartBaseImage(epd.getbuffer(time_image))
    
    time_draw = ImageDraw.Draw(time_image)

    epd.init(1) # into partial refresh mode
    button_a = Button(13)
    button_b = Button(19)
    button_c = Button(26)
    button_a.when_pressed = on_button_a_pressed
    button_b.when_pressed = on_button_b_pressed
    button_c.when_pressed = on_button_c_pressed
    while (True):
        if changed():
            time_draw.rectangle((10, 10, 120, 50), fill = 255)
            time_draw.text((10, 10), msg, font = font, fill = 0)
            epd.displayPart(epd.getbuffer(time_image))
        else:
            logging.info("no changes, sleep...")
            time.sleep(1)

    logging.info("Clear...")
    epd.init(0)
    epd.Clear(0xFF)

    logging.info("Goto Sleep...")
    epd.sleep()

except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd1in54_V2.epdconfig.module_exit()
    exit()
