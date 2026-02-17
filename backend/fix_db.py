import re 
with open('routes_auth.py', 'r') as f: 
    content = f.read() 
content = re.sub(r'def get_db\(\):.*?return _db', 'def get_db():\\n    \"\"\"Get SQLAlchemy db instance.\"\"\"\\n    global _db\\n    return _db', content, flags=re.DOTALL) 
content = re.sub(r'def get_mail\(\):.*?return _mail', 'def get_mail():\\n    \"\"\"Get mail instance.\"\"\"\\n    global _mail\\n    return _mail', content, flags=re.DOTALL) 
with open('routes_auth.py', 'w') as f: 
    f.write(content) 
print('Fixed!') 
