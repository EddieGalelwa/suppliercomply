import os 
old = '254700000000' 
new = '254724896761' 
files = ['frontend/templates/base.html', 'frontend/templates/index.html', 'frontend/templates/upgrade.html'] 
for file in files: 
    with open(file, 'r', encoding='utf-8') as f: content = f.read() 
    content = content.replace(old, new) 
    with open(file, 'w', encoding='utf-8') as f: f.write(content) 
    print(f'Updated: {file}') 
print('Done!') 
