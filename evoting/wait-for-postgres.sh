#!/bin/sh
# wait-for-postgres.sh

set -e

host="$1"
shift
cmd="$@"

until PGPASSWORD=$DJANGO_DB_PASSWORD psql -h "$host" -U "$DJANGO_DB_USER" -d "$DJANGO_DB_NAME" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata ./dbinit/initial_data.json
python manage.py create_temp_voter

PGPASSWORD=$DJANGO_DB_PASSWORD psql -h "$host" -U "$DJANGO_DB_USER" -d "$DJANGO_DB_NAME" -f ./dbinit/db_init.sql

exec $cmd