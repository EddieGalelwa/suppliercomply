from app import create_app 
app = create_app() 
with app.app_context(): 
    db = app.extensions['sqlalchemy'] 
    print(f'db type: {type(db)}') 
    print(f'db.session: {db.session}') 
    from app import User 
    print(f'User: {User}') 
    user_count = User.query.count() 
    print(f'User count: {user_count}') 
