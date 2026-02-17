with open('routes_auth.py', 'r') as f: 
    lines = f.readlines() 
 
# Find where the duplicate starts (line 46 - index 45) 
# Remove lines 45-48 (indices 45-48) which are the duplicate 
new_lines = lines[:45]  # Keep up to line 45 (Activity line) 
new_lines.extend(lines[49:])  # Skip lines 46-49 and continue from line 50 
 
with open('routes_auth.py', 'w') as f: 
    f.writelines(new_lines) 
 
print('Fixed indentation error') 
