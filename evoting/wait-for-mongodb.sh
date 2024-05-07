#!/bin/sh
# wait-for-mongodb.sh

set -e

host="$1"
shift
cmd="$@"

# Wait for MongoDB to be ready
until mongosh --host "$host" --username "$DJANGO_DB_USER" --password "$DJANGO_DB_PASSWORD" --authenticationDatabase "admin" --eval "db.stats()" > /dev/null; do
  >&2 echo "MongoDB is unavailable - sleeping"
  sleep 1
done

>&2 echo "MongoDB is up - executing command"
exec $cmd
