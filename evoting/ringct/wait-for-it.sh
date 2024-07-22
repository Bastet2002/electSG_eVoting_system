#!/bin/bash

# wait-for-it.sh

set -e

host="$1"
shift
cmd="$@"

until psql $DATABASE_URL -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

# until PGPASSWORD=$RINGCT_DB_PASSWORD psql -h "$RINGCT_DB_HOST" -U "$RINGCT_DB_USER" -d "$RINGCT_DB_NAME" -c '\q'; do
#   >&2 echo "RingCT Postgres is unavailable - sleeping"
#   sleep 1
# done


exec $cmd