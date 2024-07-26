#!/bin/bash
# wait-for-postgres.sh

set -e

# wait for the ringct database is up, and ringct database could create the db table needed
initial_wait=5

>&2 echo "Waiting for $initial_wait seconds for the ringct database to be up"
sleep $initial_wait

wait_for_postgres() {
  until psql $DATABASE_URL -c '\q'; do
    >&2 echo "Postgres is unavailable - sleeping"
    sleep 1
  done
}

drop_all_user_tables() {
  >&2 echo "Dropping all user tables in the database..."
  psql $DATABASE_URL <<EOF
DO \$\$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END \$\$;
EOF
  >&2 echo "All user tables dropped."
}

wait_for_postgres
drop_all_user_tables

export PYTHONPATH=/app:$PYTHONPATH

>&2 echo "Postgres is up - executing command"
command psql $DATABASE_URL -f ./ringct/dbinit/db_init.sql
command python manage.py makemigrations 
command python manage.py migrate 
command python manage.py loaddata ./dbinit/initial_data.json
command python manage.py create_election_phase
command python manage.py create_admin_acc
command python manage.py create_district_data
command python manage.py create_mock_singpass_data
command python manage.py create_candidate_data

# python ./pygrpc/test_init.py # TODO: remove this line after testing, activate pooling day now

# production grade deployment 
if [ "$ENVIRONMENT" = "dev" ]; then 
  echo "Running in aws development"
  command python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 evoting.wsgi:application 
else
  echo "Running in local development"
  command python manage.py collectstatic --noinput && python manage.py runsslserver 0.0.0.0:8000 --certificate /app/ssl/localhost.crt --key /app/ssl/localhost.key
fi