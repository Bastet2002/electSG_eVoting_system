districts_mocked = ['CLEMENTI', 'JURONG EAST', 'CENTRAL']
# voternum_per_district = 50 # for stress test
# voternum_per_district = 20 # for normal deployment
voternum_per_district = 500 # for sql performance test
candidate_num_total = 15
randomseed = 9
def write_csv(data=list(), file_path='singpass_login.csv'):
    with open(file_path, 'w') as f:
        for item in data:
            f.write(f"{item}\n")
    f.close()