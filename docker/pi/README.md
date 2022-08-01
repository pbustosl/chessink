```
cd ~/git/chessink/docker/pi
docker kill chesspi && docker rm chesspi
docker build -t chesspi .
docker run --name chesspi -d chesspi
docker exec -it chesspi bash
```
