#!/bin/bash
# start.sh

./wait-for-mongodb.sh db

# maybe it is not done like this for djongo
echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Starting Django..."