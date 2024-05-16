# Use an official Ubuntu as a parent image
FROM ubuntu:latest

# Avoid prompts from apt-get
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    g++ \
    make \
    libsodium-dev

WORKDIR /app

COPY . /app

# change to makefile or cmake later
RUN g++ -o myapp lsag.cpp -lsodium 

CMD ["./myapp"]
