with open('routes_auth.py', 'r') as f: 
    lines = f.readlines() 
new_lines = lines[:36] 
new_lines.append('    # Import models directly from app module (safe because we are in request context)\n') 
new_lines.append('    import sys\n') 
new_lines.append('    app_module = sys.modules.get("app")\n') 
new_lines.append('    if app_module is None:\n') 
new_lines.append('        # Fallback: import app directly\n') 
new_lines.append('        import app as app_module\n') 
new_lines.append('\n') 
new_lines.append('    User = getattr(app_module, "User", None)\n') 
new_lines.append('    Activity = getattr(app_module, "Activity", None)\n') 
new_lines.extend(lines[43:]) 
with open('routes_auth.py', 'w') as f: 
    f.writelines(new_lines) 
print('Fixed!') 
