#!/usr/bin/python
# -*- coding:utf-8 -*-

CS_URL = 'http://localhost:9000'

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

import urllib.request
import json
def cs_start_board():
    with urllib.request.urlopen(CS_URL) as response:
        body = response.read()
        res_data = json.loads(body)
        return res_data['board']
def cs_play(board_fen, move):
    req_data = {'board': board_fen, 'move': move, 'max_time_s': 1.0 }
    req =  urllib.request.Request(CS_URL, data=json.dumps(req_data).encode('utf-8'))
    with urllib.request.urlopen(req) as response:
        body = response.read()
        res_data = json.loads(body)
        board_fen = res_data['board']
        return board_fen, res_data['move']

def on_button_a_pressed():
    on_button_pressed('a')
def on_button_b_pressed():
    on_button_pressed('b')
def on_button_c_pressed():
    on_button_pressed('c')

def on_button_pressed(id):
    global mutex
    if mutex.acquire(False):
        process_button_move(id)
        time.sleep(0.15) # "pressed" triggers multiple events for more than 0.1s
        mutex.release()
def process_button_move(button):
    global move
    global movei
    if button == 'c':
        if move[movei] != 0:
            movei += 1
    else:
        incr = 1 if button == 'a' else 4
        move[movei] = (move[movei] + incr) % 9
def changed():
    global move
    global movet
    res = (move != movet)
    if res:
        movet = move.copy()
    return res


def move2str(move): # e.g. 4244 -> d2d4
    aux = [0,0,0,0]
    for i, x in enumerate(move):
        if x == 0:
            aux[i] = '_'
        else:
            if i % 2 == 0:
                aux[i] = chr(ord('a')+x-1)
            else:
                aux[i] = x
    return ''.join(str(x) for x in aux)


move = [0,0,0,0]
movet = None
movei = 0
mutex = Lock()
board_fen = cs_start_board()

button_a = Button(13)
button_b = Button(19)
button_c = Button(26)
button_a.when_pressed = on_button_a_pressed
button_b.when_pressed = on_button_b_pressed
button_c.when_pressed = on_button_c_pressed

try:
    logging.info("init epd1in54_V2")
    
    epd = epd1in54_V2.EPD()
    epd.init(0)
    epd.Clear(0xFF)
    
    # partial update
    logging.info("displayPartBaseImage")
    font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
    chess_image = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
    epd.displayPartBaseImage(epd.getbuffer(chess_image))
    
    chess_draw = ImageDraw.Draw(chess_image)

    epd.init(1) # into partial refresh mode
    while (True):
        if movei == 4:
            logging.info(f"black move: {move2str(move)}")
            try:
                board_fen, cs_move = cs_play(board_fen, move2str(move))
                move = [0,0,0,0]
                movei = 0
                chess_draw.rectangle((10, 50, 120, 100), fill = 255)
                chess_draw.text((10, 50), f"bk: {cs_move}", font = font, fill = 0)
                epd.displayPart(epd.getbuffer(chess_image))
            except Exception as e:
                move = [0,0,0,0]
                movei = 0
                logging.error(e)
        if changed():
            logging.info("drawing changes")
            chess_draw.rectangle((10, 10, 120, 50), fill = 255)
            chess_draw.text((10, 10), f"wt: {move2str(move)}", font = font, fill = 0)
            epd.displayPart(epd.getbuffer(chess_image))
        else:
            logging.info("no changes, sleep...")
            time.sleep(1)

    logging.info("clear...")
    epd.init(0)
    epd.Clear(0xFF)

    logging.info("sleep...")
    epd.sleep()

except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd1in54_V2.epdconfig.module_exit()
    exit()
