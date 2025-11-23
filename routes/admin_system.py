import json
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from mysql.connector import Error
from db import get_db_connection
from auth_utils import permission_required

def register(app):
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        return render_template('admin/dashboard.html', user=current_user)

    # --- SETTINGS ---
    @app.route('/admin/settings', methods=['GET', 'POST'])
    @login_required
    def admin_settings():
        # Basic role check - only admins should see this
        if current_user.role_name != 'Administrator':
            flash('Access denied', 'danger')
            return redirect(url_for('admin_dashboard'))
            
        if request.method == 'POST':
            try:
                limit = int(request.form.get('upload_limit', 50))
                current_app.config['UPLOAD_ROW_LIMIT'] = limit
                flash('Settings updated successfully.', 'success')
            except ValueError:
                flash('Invalid input for limit.', 'danger')
        
        current_limit = current_app.config.get('UPLOAD_ROW_LIMIT', 50)
        return render_template('admin/settings.html', upload_limit=current_limit)

    # --- USERS ---
    @app.route('/admin/users')
    @login_required
    def admin_users():
        if not current_user.can('users', 'read'):
            flash('Access denied', 'danger')
            return redirect(url_for('admin_dashboard'))
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT u.*, r.name as role_name FROM users u JOIN roles r ON u.role_id = r.id")
        users = cursor.fetchall()
        cursor.execute("SELECT * FROM roles")
        roles = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin/users.html', users=users, roles=roles)

    @app.route('/admin/users/add', methods=['POST'])
    @login_required
    @permission_required('users', 'create')
    def add_user():
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role_id = request.form['role_id']
        pwd_hash = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role_id, updated_by) VALUES (%s, %s, %s, %s, %s)",
                (username, email, pwd_hash, role_id, current_user.username)
            )
            conn.commit()
            flash('User added successfully', 'success')
        except Error as e:
            flash(f'Error: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/delete/<int:user_id>')
    @login_required
    @permission_required('users', 'delete')
    def delete_user(user_id):
        if user_id == current_user.id:
            flash("You cannot delete yourself", "warning")
            return redirect(url_for('admin_users'))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('User deleted', 'success')
        return redirect(url_for('admin_users'))

    # --- ROLES ---
    @app.route('/admin/roles')
    @login_required
    def admin_roles():
        if not current_user.can('roles', 'read'):
            flash('Access denied', 'danger')
            return redirect(url_for('admin_dashboard'))
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM roles")
        roles = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin/roles.html', roles=roles)

    @app.route('/admin/roles/update_bulk', methods=['POST'])
    @login_required
    @permission_required('roles', 'update')
    def admin_roles_update_bulk():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Get all roles to iterate through
        cursor.execute("SELECT id FROM roles")
        all_roles = cursor.fetchall()
        
        resources = ['users', 'roles', 'issues', 'small_claims', 'statutes', 'approvals', 'logs']
        actions = ['create', 'read', 'update', 'delete']
        
        try:
            for role in all_roles:
                role_id = role['id']
                new_perms = {}
                
                for res in resources:
                    new_perms[res] = {}
                    for act in actions:
                        # Key format matches template: perm_{role.id}_{res_key}_{action}
                        key = f"perm_{role_id}_{res}_{act}"
                        new_perms[res][act] = 1 if key in request.form else 0
                
                perm_json = json.dumps(new_perms)
                
                cursor.execute(
                    "UPDATE roles SET permissions = %s, updated_by = %s, updated_dt = NOW() WHERE id = %s",
                    (perm_json, current_user.username, role_id)
                )
            
            conn.commit()
            flash('All role permissions updated successfully.', 'success')
            
        except Error as e:
            flash(f'Database Error: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
            
        return redirect(url_for('admin_roles'))

    # Keeping old single update route for backward compatibility if needed by other views
    @app.route('/admin/roles/update/<int:role_id>', methods=['POST'])
    @login_required
    @permission_required('roles', 'update')
    def update_role(role_id):
        # Added 'logs' to resources list to support the new UI option
        resources = ['users', 'roles', 'issues', 'small_claims', 'statutes', 'approvals', 'logs']
        actions = ['create', 'read', 'update', 'delete']
        new_perms = {}
        for res in resources:
            new_perms[res] = {}
            for act in actions:
                key = f"perm_{res}_{act}"
                new_perms[res][act] = 1 if key in request.form else 0
        perm_json = json.dumps(new_perms)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE roles SET permissions = %s, updated_by = %s, updated_dt = NOW() WHERE id = %s",
            (perm_json, current_user.username, role_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Role permissions updated', 'success')
        return redirect(url_for('admin_roles'))