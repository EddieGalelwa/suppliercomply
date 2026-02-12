import re 
with open('app.py', 'r') as f: 
    content = f.read() 
content = re.sub(r'\"\"\"\s*from dotenv import load_dotenv\s*load_dotenv\(\)\s*', '\"\"\"\n', content) 
content = content.replace('Main Flask Application Entry Point\n\"\"\"\n\nimport os', 'Main Flask Application Entry Point\n\"\"\"\n\nfrom dotenv import load_dotenv\nload_dotenv()\n\nimport os') 
with open('app.py', 'w') as f: 
    f.write(content) 
print('Fixed!') 
