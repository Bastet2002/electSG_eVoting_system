# Use an official Ubuntu as a parent image
FROM ubuntu:latest

# Avoid prompts from apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Update packages and install the necessary packages
RUN apt-get update && apt-get install -y \
    g++ \
    make \
    libsodium-dev

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Compile the C++ program (adjust the file names as necessary)
RUN g++ -o myapp commitment.cpp -lsodium

# Command to run the compiled program
CMD ["./myapp"]
