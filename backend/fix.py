import re 
with open('routes_auth.py', 'r') as f: 
    content = f.read() 
content = re.sub(r'from app import db, mail, User, Activity\s*$', '', content, flags=re.MULTILINE) 
if 'from app import' not in content.split('# Import here')[-1]: 
    content += '\n\n# Import here to avoid circular import\nfrom app import db, mail, User, Activity\n' 
with open('routes_auth.py', 'w') as f: 
    f.write(content) 
print('Fixed!') 
