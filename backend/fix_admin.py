import re 
with open('routes_admin.py', 'r') as f: 
    content = f.read() 
content = content.replace('import logging', 'import logging\nfrom functools import wraps') 
content = content.replace('def decorated_function(*args, **kwargs):', '@wraps(f)\n    def decorated_function(*args, **kwargs):') 
with open('routes_admin.py', 'w') as f: 
    f.write(content) 
print('Fixed!') 
