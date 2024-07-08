#!/bin/bash

# wait-for-it.sh

set -e

host="$1"
shift
cmd="$@"

until PGPASSWORD=$DJANGO_DB_PASSWORD psql -h "$DJANGO_DB_HOST" -U "$DJANGO_DB_USER" -d "$DJANGO_DB_NAME" -c '\q'; do
  >&2 echo "Django Postgres is unavailable - sleeping"
  sleep 1
done

until PGPASSWORD=$RINGCT_DB_PASSWORD psql -h "$RINGCT_DB_HOST" -U "$RINGCT_DB_USER" -d "$RINGCT_DB_NAME" -c '\q'; do
  >&2 echo "RingCT Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

PGPASSWORD=$RINGCT_DB_PASSWORD psql -h "$RINGCT_DB_HOST" -U "$RINGCT_DB_USER" -d "$RINGCT_DB_NAME" -f ./dbinit/db_init.sql

exec $cmd
