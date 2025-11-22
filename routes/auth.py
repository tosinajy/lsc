from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from db import get_db_connection
from auth_utils import load_user_from_db

def register(app):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('admin_dashboard'))
            
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Fetch user
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            
            # Prepare log data
            ip_addr = request.remote_addr
            user_agent = request.headers.get('User-Agent')
            
            if user_data and check_password_hash(user_data['password_hash'], password):
                # Log Success
                cursor.execute(
                    "INSERT INTO login_logs (username_attempted, status, ip_address, user_agent) VALUES (%s, 'SUCCESS', %s, %s)",
                    (username, ip_addr, user_agent)
                )
                conn.commit()
                
                # Perform Login
                user_obj = load_user_from_db(user_data['id'])
                login_user(user_obj)
                
                cursor.close()
                conn.close()
                return redirect(url_for('admin_dashboard'))
            else:
                # Log Failure
                cursor.execute(
                    "INSERT INTO login_logs (username_attempted, status, ip_address, user_agent) VALUES (%s, 'FAILURE', %s, %s)",
                    (username, ip_addr, user_agent)
                )
                conn.commit()
                
                cursor.close()
                conn.close()
                flash('Invalid username or password', 'danger')
                
        return render_template('admin/login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))