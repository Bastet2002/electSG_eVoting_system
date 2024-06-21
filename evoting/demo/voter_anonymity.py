import psycopg2
import os
import json

voter_id = 1
# the first record of voting currency and vote record belongs to the voter_id 1
# in the future, we will randomize the order
district_id = 1
ic = 'A1234567B'

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

print(f"Accessing the voter anonymity of voter {ic} with voter_id {voter_id} in district {district_id}")
# --------------------------------------
# all stealth addresses of district 1 (clementi)
try:
    clementi_sa = f"select stealth_address from myapp_votingcurrency where district_id={district_id};"
    cur.execute(clementi_sa)
    sa_result = cur.fetchall()
    print("=" * 50)
    print(f"Printing all stealth addresses of district {district_id} (clementi)")
    print("=" * 50)
    if sa_result:
        count = 0
        for sa in sa_result:
            count += 1
            print(f'{count:<3}: {sa[0]}')
except Exception as e:
    print(f"Error executing query: {e}")
print()

# --------------------------------------
# voting curr of the voter id 1
try:
    voting_curr = f"select stealth_address, commitment_record from myapp_votingcurrency where id={voter_id};"
    cur.execute(voting_curr)
    vc_result = cur.fetchone()
    if vc_result:
        print("=" * 50)
        print(f"Querying the voting currency of voter id {voter_id}")
        print("=" * 50)
        sa = vc_result[0]
        vc_json = vc_result[1]
        print(f'{"stealth address":<20}: {sa}')
        print(f'{"rG":<20}: {vc_json.get("rG")}')
        commitment = vc_json.get("commitment")
        print(f'{"input commitment":<20}: {commitment.get("input_commitment")}')
        print(f'{"output commitment":<20}: {commitment.get("output_commitment")}')
        print(f'{"pseudoout commitment":<20}: {commitment.get("pseudoout_commitment")}')
        print(f'{"amount mask":<20}: {commitment.get("amount_mask")}')
    else:
        print("No result found")
except Exception as e:
    print(f"Error executing query: {e}")
print()
# --------------------------------------
# vote record of voter id 1
try:
    # this assume the first record is performed by voter id 1
    voting_curr = f"select key_image, transaction_record from myapp_voterecords;"
    cur.execute(voting_curr)
    vc_result = cur.fetchone()
    if vc_result:
        print("=" * 50)
        print(f"Querying the vote record of voter id {voter_id}")
        print("=" * 50)
        ki = vc_result[0]
        vr_json = vc_result[1]

        print(f'{"key image":<20}: {ki}')
        print(f'{"rG":<20}: {vc_result[1].get("rG")}')
        print(f'{"stealth address":<20}: {vc_result[1].get("stealth_address")}')

        print('-'*20)
        cmt = vc_result[1].get("commitment")
        print('Commitment')
        print(f'{"":<5}{"output commitment":<20}: {commitment.get("output_commitment")}')
        print(f'{"":<5}{"pseudoout commitment":<20}: {commitment.get("pseudoout_commitment")}')
        print(f'{"":<5}{"amount mask":<20}: {commitment.get("amount_mask")}')

        print('-'*20)
        blsag = vc_result[1].get("blsagSig")
        print('Linkable Ring Signature')
        print(f'{"":<5}{"challenge":<20}: {blsag.get("c")}')
        print(f'{"":<5}{"message":<20}: {blsag.get("m")}')
        print(f'{"":<5}{"response":<20}:')
        count = 0
        for res in blsag.get("r"):
            count += 1
            print(f'{"":<8}{f"r {count}":<20}: {res}')
        print(f'{"":<5}{"ring member":<20}:')
        count = 0
        for res in blsag.get("members"):
            count += 1
            print(f'{"":<8}{f"member {count}":<20}: {res}')
        
    else:
        print("No result found")
except Exception as e:
    print(f"Error executing query: {e}")
cur.close()
conn.close()