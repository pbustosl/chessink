#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
picdir = os.path.join(os.environ["WAVESHARE_DIR"], 'pic')
libdir = os.path.join(os.environ["WAVESHARE_DIR"], 'lib')
sys.path.append(libdir)

import logging
from waveshare_epd import epd1in54_V2
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

logging.basicConfig(level=logging.DEBUG)

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
    num = 0
    while (True):
        time_draw.rectangle((10, 10, 120, 50), fill = 255)
        time_draw.text((10, 10), time.strftime('%H:%M:%S'), font = font, fill = 0)
        epd.displayPart(epd.getbuffer(time_image))
        num = num + 1
        if(num == 5):
            break
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
