with open('.env', 'r') as f: 
    content = f.read() 
content = content.replace('CLOUDINARY_CLOUD_NAME=your-cloud-name', 'CLOUDINARY_CLOUD_NAME=dpgnxxlzp') 
content = content.replace('CLOUDINARY_API_KEY=your-api-key', 'CLOUDINARY_API_KEY=561427414672689') 
content = content.replace('CLOUDINARY_API_SECRET=your-api-secret', 'CLOUDINARY_API_SECRET=rg-TVxoLxJtXeGXV5IUZsu5u6zs') 
with open('.env', 'w') as f: 
    f.write(content) 
print('Cloudinary credentials updated!') 
