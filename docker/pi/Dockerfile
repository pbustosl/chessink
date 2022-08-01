FROM debian:10.11

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
  g++ \
  make \
  wget \
  python3 \
  python3-pip \
  unzip \
  && rm -rf /var/lib/apt/lists/*

RUN pip3 install chess

# install Stockfish
WORKDIR /root/
RUN wget https://github.com/official-stockfish/Stockfish/archive/sf_15.zip
RUN unzip sf_15.zip
WORKDIR /root/Stockfish-sf_15/src
RUN make build ARCH=armv8
WORKDIR /root/

CMD ["/usr/bin/tail", "-f" , "/dev/null"]
