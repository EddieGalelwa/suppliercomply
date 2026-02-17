from app import app, create_app 
app = create_app() 
with app.app_context(): 
    print('Extensions:', list(app.extensions.keys())) 
    for key in app.extensions: 
        print(f'{key}: {app.extensions[key].__class__.__name__}') 
