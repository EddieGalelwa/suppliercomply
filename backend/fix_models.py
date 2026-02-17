import re 
with open('routes_auth.py', 'r') as f: 
    content = f.read() 
 
# Replace the get_models function 
old_get_models = '''def get_models(): 
    \"\"\"Get all models and extensions from current app.\"\"\" 
    # Access through current_app to avoid circular imports 
    from flask import current_app 
    from sqlalchemy import inspect 
 
    # Get the SQLAlchemy instance 
    db = current_app.extensions.get('sqlalchemy') 
    if db is None: 
        # Try getting it from the app directly 
        db = getattr(current_app, 'extensions', {}).get('sqlalchemy') 
 
    # Get Mail instance 
    mail = current_app.extensions.get('mail') 
    if mail is None: 
        mail = getattr(current_app, 'extensions', {}).get('mail') 
 
    # Get models from the db.Model registry 
    # We need to access them through the db.Model registry 
    User = db.Model._decl_class_registry.get('User') 
    Activity = db.Model._decl_class_registry.get('Activity') 
 
    # If that doesn't work, try getting from the app's module 
    if User is None: 
        import sys 
        app_module = sys.modules.get('app') 
        if app_module: 
            User = getattr(app_module, 'User', None) 
            Activity = getattr(app_module, 'Activity', None) 
 
    return db, mail, User, Activity''' 
 
new_get_models = '''def get_models(): 
    \"\"\"Get all models and extensions from current app.\"\"\" 
    from flask import current_app 
 
    # Get the SQLAlchemy instance 
    db = current_app.extensions.get('sqlalchemy') 
    if db is None: 
        db = getattr(current_app, 'extensions', {}).get('sqlalchemy') 
 
    # Get Mail instance 
    mail = current_app.extensions.get('mail') 
    if mail is None: 
        mail = getattr(current_app, 'extensions', {}).get('mail') 
 
    # Import models directly from app module (safe because we're in request context) 
    import sys 
    app_module = sys.modules.get('app') 
    if app_module is None: 
        # Fallback: import app directly 
        import app as app_module 
 
    User = getattr(app_module, 'User', None) 
    Activity = getattr(app_module, 'Activity', None) 
 
    return db, mail, User, Activity''' 
 
content = content.replace(old_get_models, new_get_models) 
 
with open('routes_auth.py', 'w') as f: 
    f.write(content) 
print('Fixed get_models() function') 
