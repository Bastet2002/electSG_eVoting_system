# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE evoting.settings 

# Set the working directory in the container
WORKDIR /app

# Install MongoDB Shell (mongosh)
RUN apt-get update && apt-get install -y wget gnupg \
    && wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | apt-key add - \
    && echo "deb http://repo.mongodb.org/apt/debian buster/mongodb-org/7.0 main" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list \
    && apt-get update \
    && apt-get install -y mongodb-mongosh

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app/
COPY . /app/

RUN chmod +x ./wait-for-mongodb.sh

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["./wait-for-mongodb.sh", "db", "python", "manage.py", "runserver", "0.0.0.0:8000"]

