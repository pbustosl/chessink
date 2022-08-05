#!/usr/bin/python
# -*- coding:utf-8 -*-

CHESS_SERVER_URL = 'http://localhost:9000'
CHESS_SERVER_MAX_TIME_S = 1.0
BUTTON_BCM = {
    'A': 13, # +1
    'B': 19, # +4
    'C': 26, # next
}

#####################################################
import urllib.request
import json

class ChessEngine:

    def __init__(self, chess_server_url):
        self.chess_server_url = chess_server_url
        self.board_fen = None

    def reset_board(self):
        with urllib.request.urlopen(self.chess_server_url) as response:
            body = response.read()
            res_data = json.loads(body)
            self.board_fen = res_data['board']

    def play(self, move):
        req_data = {'board': self.board_fen, 'move': move, 'max_time_s': CHESS_SERVER_MAX_TIME_S }
        req =  urllib.request.Request(self.chess_server_url, data=json.dumps(req_data).encode('utf-8'))
        with urllib.request.urlopen(req) as response:
            body = response.read()
            res_data = json.loads(body)
            self.board_fen = res_data['board']
            return res_data['move']

#####################################################

from threading import Lock

import sys
import os
libdir = os.path.join(os.environ["WAVESHARE_DIR"], 'lib')
sys.path.append(libdir)

from gpiozero import Button

import logging
from waveshare_epd import epd1in54_V2
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

logging.basicConfig(level=logging.DEBUG)

def on_button_pressed(button):
    global mutex
    if mutex.acquire(False):
        try:
            process_button_move(button)
            time.sleep(0.15) # "pressed" triggers multiple events for more than 0.1s
        except Exception as e:
            logging.error(e)
        finally:
            mutex.release()
def process_button_move(button):
    logging.info(button.pin.number)
    global move
    global movei
    if button.pin.number == BUTTON_BCM['C']:
        if move[movei] != 0:
            movei += 1
    else:
        incr = 1 if button.pin.number == BUTTON_BCM['A'] else 4
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


chess_engine = ChessEngine(CHESS_SERVER_URL)
chess_engine.reset_board()
move = [0,0,0,0]
movet = None
movei = 0
mutex = Lock()

for x in BUTTON_BCM:
    button = Button(BUTTON_BCM[x])
    button.when_pressed = on_button_pressed

try:
    logging.info("init epd1in54_V2")
    
    epd = epd1in54_V2.EPD()
    epd.init(0)
    epd.Clear(0xFF)
    
    # partial update
    logging.info("displayPartBaseImage")
    # https://ttfonts.net/font/11165_Courier.htm
    font = ImageFont.truetype('/home/pi/utils/09809_COURIER.ttf', 28)
    chess_image = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
    epd.displayPartBaseImage(epd.getbuffer(chess_image))
    
    chess_draw = ImageDraw.Draw(chess_image)

    epd.init(1) # into partial refresh mode
    while (True):
        if movei >= 4:
            logging.info(f"black move: {move2str(move)}")
            if move2str(move) == 'a1a1':
                logging.info("reset game")
                move = [0,0,0,0]
                movet = None
                movei = 0
                chess_engine.reset_board()
                chess_draw.rectangle((10, 50, epd.width - 10, 100), fill = 255)
                epd.displayPart(epd.getbuffer(chess_image))
            else:
                try:
                    engine_move = chess_engine.play(move2str(move))
                    move = [0,0,0,0]
                    movei = 0
                    chess_draw.rectangle((10, 50, epd.width - 10, 100), fill = 255)
                    chess_draw.text((10, 50), f"b: {engine_move}", font = font, fill = 0)
                    epd.displayPart(epd.getbuffer(chess_image))
                except Exception as e:
                    move = [0,0,0,0]
                    movei = 0
                    logging.error(e)
        if changed():
            logging.info("drawing changes")
            chess_draw.rectangle((10, 10, epd.width - 10, 50), fill = 255)
            chess_draw.text((10, 10), f"w: {move2str(move)}", font = font, fill = 0)
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
