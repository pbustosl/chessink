#!/usr/bin/python
# -*- coding:utf-8 -*-

CHESS_SERVER_URL = 'http://localhost:9000'
CHESS_SERVER_MAX_TIME_S = 1.0
BUTTON_BCM = {
    'A': 13, # +1
    'B': 19, # +4
    'C': 26, # next
}

import logging
logging.basicConfig(level=logging.DEBUG)

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
from gpiozero import Button

class Player:

    def __init__(self):
        self.reset()
        self.mutex = Lock()
        for x in BUTTON_BCM:
            button = Button(BUTTON_BCM[x])
            button.when_pressed = self.on_button_pressed

    def reset(self):
        self.move = [0,0,0,0]
        self.movet = None
        self.movei = 0

    def on_button_pressed(self, button):
        if self.mutex.acquire(False):
            try:
                self.process_button_move(button)
                time.sleep(0.15) # button pressed triggers multiple events for more than 0.1s, skip them
            except Exception as e:
                logging.error(e)
            finally:
                self.mutex.release()

    def process_button_move(self, button):
        logging.info(f"button pressed: {button.pin.number}")
        if button.pin.number == BUTTON_BCM['C']:
            if self.move[self.movei] != 0:
                self.movei += 1
        else:
            incr = 1 if button.pin.number == BUTTON_BCM['A'] else 4
            self.move[self.movei] = (self.move[self.movei] + incr) % 9

    def playing(self):
        res = (self.move != self.movet)
        if res:
            self.movet = self.move.copy()
        return res

    def moved(self):
        return self.movei >= 4

    def get_move(self):
        # e.g. 4240 -> d2d_
        aux = [0,0,0,0]
        for i, x in enumerate(self.move):
            if x == 0:
                aux[i] = '_'
            else:
                if i % 2 == 0:
                    aux[i] = chr(ord('a')+x-1)
                else:
                    aux[i] = x
        return ''.join(str(x) for x in aux)

#####################################################

import sys
import os
libdir = os.path.join(os.environ["WAVESHARE_DIR"], 'lib')
sys.path.append(libdir)

from waveshare_epd import epd1in54_V2
import time
from PIL import Image,ImageDraw,ImageFont

chess_engine = ChessEngine(CHESS_SERVER_URL)
chess_engine.reset_board()

player = Player()

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
        if player.moved():
            logging.info(f"black move: {player.get_move()}")
            if player.get_move() == 'a1a1':
                logging.info("reset game")
                player.reset()
                chess_engine.reset_board()
                chess_draw.rectangle((10, 50, epd.width - 10, 100), fill = 255)
                epd.displayPart(epd.getbuffer(chess_image))
            else:
                try:
                    engine_move = chess_engine.play(player.get_move())
                    player.reset()
                    chess_draw.rectangle((10, 50, epd.width - 10, 100), fill = 255)
                    chess_draw.text((10, 50), f"b: {engine_move}", font = font, fill = 0)
                    epd.displayPart(epd.getbuffer(chess_image))
                except Exception as e:
                    player.reset()
                    logging.error(e)
        if player.playing():
            logging.info("drawing changes")
            chess_draw.rectangle((10, 10, epd.width - 10, 50), fill = 255)
            chess_draw.text((10, 10), f"w: {player.get_move()}", font = font, fill = 0)
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
