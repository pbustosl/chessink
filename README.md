# chessink

### service

Laptop:
```
[~/git/chessink]$ scp utils/chess*.service rb:/etc/systemd/system/
[~/git/chessink]$ scp utils/chess*.sh rb:/usr/local/bin/
```

Server:
```
sudo systemctl daemon-reload

sudo systemctl enable chess_server.service
sudo systemctl start chess_server.service
sudo systemctl status chess_server.service

sudo systemctl enable chessink.service
sudo systemctl start chessink.service
sudo systemctl status chessink.service
```
