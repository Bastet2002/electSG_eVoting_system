import psycopg2
import os

conn_params = {
    'host': os.environ.get('DJANGO_DB_HOST'),  
    'port': os.environ.get('DJANGO_DB_PORT'),  
    'dbname': os.environ.get('DJANGO_DB_NAME'), 
    'user': os.environ.get('DJANGO_DB_USER'),   
    'password': os.environ.get('DJANGO_DB_PASSWORD') 
}

try:
    conn = psycopg2.connect(**conn_params)
    print("Connection successful")
except Exception as e:
    print(f"Unable to connect to the database: {e}")

cur = conn.cursor()

query = "SELECT version();"

# Execute the query
try:
    cur.execute(query)
    result = cur.fetchone()
    print("Query result:", result)
except Exception as e:
    print(f"Error executing query: {e}")

cur.close()
conn.close()

# get the voter_id
# get the stealth addrss
# get the key_image
# get the commitment

voting_curr = "select * from myapp_voting_currency where voter_id=1;"
vote_record = "select * from myapp_vote_records;"