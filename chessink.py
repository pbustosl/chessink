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
        self.reset_board()

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
from PIL import Image,ImageDraw,ImageFont

class ChessDisplay:
    def __init__(self):
        # https://ttfonts.net/font/11165_Courier.htm
        self.font = ImageFont.truetype('/home/pi/utils/09809_COURIER.ttf', 28)

        logging.info("init epd1in54_V2")
        self.epd = epd1in54_V2.EPD()
        self.epd.init(0)
        self.epd.Clear(0xFF)
        # partial update
        logging.info("displayPartBaseImage")
        self.chess_image = Image.new('1', (self.epd.width, self.epd.height), 255)  # 255: clear the frame
        self.epd.displayPartBaseImage(self.epd.getbuffer(self.chess_image))
        self.chess_draw = ImageDraw.Draw(self.chess_image)
        self.epd.init(1) # into partial refresh mode

    def reset(self):
        self.chess_draw.rectangle((10, 50, epd.width - 10, 100), fill = 255)
        epd.displayPart(epd.getbuffer(self.chess_image))

    def show_engine_move(self, move):
        self.chess_draw.rectangle((10, 50, self.epd.width - 10, 100), fill = 255)
        self.chess_draw.text((10, 50), f"b: {move}", font = self.font, fill = 0)
        self.epd.displayPart(self.epd.getbuffer(self.chess_image))

    def show_player_move(self, move):
        self.chess_draw.rectangle((10, 10, self.epd.width - 10, 50), fill = 255)
        self.chess_draw.text((10, 10), f"w: {move}", font = self.font, fill = 0)
        self.epd.displayPart(self.epd.getbuffer(self.chess_image))

    def clear(self):
        logging.info("clear...")
        self.epd.init(0)
        self.epd.Clear(0xFF)
        logging.info("sleep...")
        self.epd.sleep()

    def exit(self):
        epd1in54_V2.epdconfig.module_exit()

#####################################################
import time

try:
    chess_engine = ChessEngine(CHESS_SERVER_URL)
    player = Player()
    display = ChessDisplay()
    while (True):
        if player.moved():
            logging.info(f"black move: {player.get_move()}")
            if player.get_move() == 'a1a1':
                logging.info("reset game")
                player.reset()
                chess_engine.reset_board()
                display.reset()
            else:
                try:
                    move = chess_engine.play(player.get_move())
                    player.reset()
                    display.show_engine_move(move)
                except Exception as e:
                    player.reset()
                    logging.error(e)
        if player.playing():
            logging.info("drawing changes")
            display.show_player_move(player.get_move())
        else:
            logging.info("no changes, sleep...")
            time.sleep(1)
    display.clear()
except IOError as e:
    logging.info(e)
except KeyboardInterrupt:
    logging.info("ctrl + c:")
    display.exit()
    exit()
