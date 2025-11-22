import json
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import UserMixin, AnonymousUserMixin, current_user
from db import get_db_connection

class User(UserMixin):
    def __init__(self, id, username, email, role_name, permissions):
        self.id = id
        self.username = username
        self.email = email
        self.role_name = role_name
        self.permissions = permissions if isinstance(permissions, dict) else json.loads(permissions)

    def can(self, resource, action):
        if self.role_name == 'Administrator':
            return True
        res = self.permissions.get(resource, {})
        return res.get(action, 0) == 1

class AnonymousUser(AnonymousUserMixin):
    def can(self, resource, action):
        return False
    @property
    def role_name(self):
        return 'Guest'
    @property
    def permissions(self):
        return {}

def load_user_from_db(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id, u.username, u.email, r.name as role_name, r.permissions
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = %s
    """, (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user_data:
        return User(
            user_data['id'], 
            user_data['username'], 
            user_data['email'], 
            user_data['role_name'],
            user_data['permissions']
        )
    return None

def permission_required(resource, action):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if not current_user.can(resource, action):
                flash('You do not have permission to perform this action.', 'danger')
                return redirect(url_for('admin_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator