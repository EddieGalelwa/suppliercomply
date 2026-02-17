import os 
with open('app.py', 'r') as f: 
    lines = f.readlines() 
with open('app.py', 'w') as f: 
    for line in lines: 
        if 'init_auth' not in line: 
            f.write(line) 
print('Removed init_auth lines') 
