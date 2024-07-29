districts_mocked = ['CLEMENTI', 'JURONG EAST', 'CENTRAL']
voternum_per_district = 50
candidate_num_total = 15
randomseed = 9
def write_csv(data=list(), file_path='singpass_login.csv'):
    with open(file_path, 'w') as f:
        for item in data:
            f.write(f"{item}\n")
    f.close()