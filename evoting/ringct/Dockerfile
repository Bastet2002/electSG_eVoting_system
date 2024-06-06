# Use an official Ubuntu as a parent image
FROM ubuntu:latest

# Avoid prompts from apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    g++ \
    make \
    libsodium-dev \
    cmake \
    build-essential \
    autoconf \
    libtool \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# note that this is different from the official grpc which is $HOME/.local
ENV MY_INSTALL_DIR=/usr/local
WORKDIR /grpc
RUN git clone --recurse-submodules -b v1.64.0 --depth 1 --shallow-submodules https://github.com/grpc/grpc .
RUN mkdir -p cmake/build && cd cmake/build \
    && cmake -DgRPC_INSTALL=ON \
    -DgRPC_BUILD_TESTS=OFF \
    -DCMAKE_INSTALL_PREFIX=$MY_INSTALL_DIR \
    ../.. \
    && make -j 4 \
    && make install

WORKDIR /app
COPY . /app

WORKDIR /app/
RUN mkdir -p build && cd build \
    && cmake -DCMAKE_PREFIX_PATH=$MY_INSTALL_DIR .. \
    && make

EXPOSE 50051

CMD ["./build/rct_server"]
