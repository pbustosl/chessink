#!/usr/bin/env bash

# location: /usr/local/bin/chessink.sh
export WAVESHARE_DIR=/home/pi/git/e-Paper/RaspberryPi_JetsonNano/python
python3 /home/pi/git/chessink/chessink.py >> /tmp/chessink.log 2>&1
