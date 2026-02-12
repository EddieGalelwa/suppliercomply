with open('app.py', 'r') as f: 
    content = f.read() 
if 'load_dotenv' not in content: 
    content = content.replace('"""', '\"\"\"\n\nfrom dotenv import load_dotenv\nload_dotenv()\n', 1) 
    with open('app.py', 'w') as f: f.write(content) 
    print('Added load_dotenv') 
else: 
    print('Already exists') 
