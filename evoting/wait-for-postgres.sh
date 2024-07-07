#!/bin/sh
# wait-for-postgres.sh

set -e

host="$1"
shift
cmd="$@"

# wait for the ringct database is up, and ringct database could create the db table needed
initial_wait=10

>&2 echo "Waiting for $initial_wait seconds for the ringct database to be up"
sleep $initial_wait

until PGPASSWORD=$DJANGO_DB_PASSWORD psql -h "$host" -U "$DJANGO_DB_USER" -d "$DJANGO_DB_NAME" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
python manage.py makemigrations 
python manage.py migrate 
python manage.py loaddata ./dbinit/initial_data.json
python manage.py create_election_phase
python manage.py create_admin_acc
python manage.py create_mock_singpass_data

# python ./pygrpc/test_init.py # this required the ringct database to be up

exec $cmd