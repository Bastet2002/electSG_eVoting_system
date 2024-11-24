# Use an official Ubuntu as a parent image
FROM ubuntu:22.04

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
    libpq-dev \
    libpqxx-dev \
    git \
    postgresql-client\
    wget

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

WORKDIR /
RUN git clone https://github.com/jtv/libpqxx.git 
WORKDIR /libpqxx
RUN git checkout 7.7

WORKDIR /app
COPY . /app

WORKDIR /app/
RUN mkdir -p build && cd build \
    && cmake -DCMAKE_PREFIX_PATH=$MY_INSTALL_DIR .. \
    && make

RUN GRPC_HEALTH_PROBE_VERSION=v0.4.28 && \
    wget -qO/bin/grpc_health_probe https://github.com/grpc-ecosystem/grpc-health-probe/releases/download/${GRPC_HEALTH_PROBE_VERSION}/grpc_health_probe-linux-amd64 && \
    chmod +x /bin/grpc_health_probe

RUN chmod +x ./wait-for-it.sh

EXPOSE 50051

CMD ["./wait-for-it.sh", "--", "./build/rct_server"]
