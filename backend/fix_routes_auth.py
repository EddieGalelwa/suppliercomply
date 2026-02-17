import re 
 
# Read the file 
with open('routes_auth.py', 'r') as f: 
    content = f.read() 
 
# Step 1: Remove the bottom import 
content = re.sub(r'\n# Import here to avoid circular import\nfrom app import db, mail, User, Activity', '', content) 
 
# Step 2: Add imports and get_db function after flask_mail import 
old_import = 'from flask_mail import Message' 
new_import = '''from flask_mail import Message 
from flask import current_app 
 
# Use current_app to avoid circular import 
def get_db(): 
    return current_app.extensions['sqlalchemy'].db''' 
content = content.replace(old_import, new_import) 
 
# Step 3: Replace all db. with get_db(). 
# But be careful not to replace in comments or strings 
