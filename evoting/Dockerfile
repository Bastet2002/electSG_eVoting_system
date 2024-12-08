# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE evoting.settings 

# Prepare grpc
RUN apt-get update && apt-get install -y git
RUN python -m pip install --upgrade setuptools==70.0.0
RUN python -m pip install grpcio grpcio-tools 
WORKDIR /grpc
RUN git clone -b v1.64.0 --depth 1 --shallow-submodules https://github.com/grpc/grpc

# Set the working directory in the container
WORKDIR /app

# it looks like the path is messed up
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y postgresql-client libpq-dev

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app/
COPY . /app/

# compile python grpc client functions
WORKDIR /app/pygrpc
RUN python -m grpc_tools.protoc -I../ringct/proto --python_out=. --pyi_out=. --grpc_python_out=. ../ringct/proto/ringct.proto 

WORKDIR /app
RUN chmod +x ./wait-for-postgres.sh

EXPOSE 8000

# Generate self-signed certificate for HTTPS
# RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /app/localhost.key -out /app/localhost.crt -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=localhost"

ENTRYPOINT [ "/bin/bash", "/app/wait-for-postgres.sh" ]