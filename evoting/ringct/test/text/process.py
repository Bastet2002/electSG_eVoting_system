
with open('./base.txt', 'r') as infile, open('./hash_infile', 'w') as outfile:
    for line in infile:
        arr = line.split()
        outfile.write(arr[1] + '\n')