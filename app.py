import datetime
import json
import math
from functools import wraps
from flask import Flask, render_template, request, abort, jsonify, Response, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, AnonymousUserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# --- Template Filters ---
@app.template_filter('from_json')
def from_json_filter(value):
    if not value:
        return {}
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return {}

# --- Auth Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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

login_manager.anonymous_user = AnonymousUser

# --- Database Connection Helper ---
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
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

# --- Context Processors ---
@app.context_processor
def inject_globals():
    return {'now': datetime.datetime.utcnow()}

# --- Public Routes ---
@app.route('/')
@app.route('/home.html')
def index():
    conn = get_db_connection()
    if not conn:
        return "Database Error", 500
    cursor = conn.cursor(dictionary=True)
    query_states = """
        SELECT DISTINCT s.name, s.slug 
        FROM states s 
        JOIN statutes st ON s.id = st.state_id 
        ORDER BY s.name ASC
    """
    cursor.execute(query_states)
    states = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('home.html', states=states)

@app.route('/api/issues/<state_slug>')
def get_issues_by_state(state_slug):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT DISTINCT i.name, i.slug
        FROM issues i
        JOIN statutes st ON i.id = st.issue_id
        JOIN states s ON st.state_id = s.id
        WHERE s.slug = %s
        ORDER BY i.name ASC
    """
    cursor.execute(query, (state_slug,))
    issues = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(issues)

@app.route('/limitations/<state_slug>/<issue_slug>')
def statute_detail(state_slug, issue_slug):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 
            s.name as state_name,
            s.state_code,
            sc.small_claims_cap,
            sc.small_claims_info,
            i.name as issue_name,
            i.description as issue_desc,
            st.duration,
            st.time_limit_type,
            st.time_limit_min,
            st.time_limit_max,
            st.details,
            st.issue_info,
            st.conditions_exceptions,
            st.examples,
            st.code_reference, 
            st.official_source_url,
            st.other_source_url,
            st.updated_dt
        FROM statutes st
        JOIN states s ON st.state_id = s.id
        JOIN issues i ON st.issue_id = i.id
        LEFT JOIN small_claims sc ON s.id = sc.state_id
        WHERE s.slug = %s AND i.slug = %s
    """
    cursor.execute(query, (state_slug, issue_slug))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not data:
        abort(404)
    return render_template('statute.html', data=data, state_slug=state_slug, issue_slug=issue_slug)

@app.route('/report-issue', methods=['POST'])
def report_issue():
    data = request.json
    print(f"ISSUE REPORTED: {data}") 
    return jsonify({'status': 'success', 'message': 'Report received.'})

@app.route('/sitemap.xml')
def sitemap():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT s.slug as state_slug, i.slug as issue_slug, st.updated_dt
        FROM statutes st
        JOIN states s ON st.state_id = s.id
        JOIN issues i ON st.issue_id = i.id
    """
    cursor.execute(query)
    urls = cursor.fetchall()
    cursor.close()
    conn.close()
    xml_sitemap = render_template('sitemap_template.xml', urls=urls, base_url=request.host_url.rstrip('/'))
    return Response(xml_sitemap, mimetype='application/xml')

# --- ADMIN ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        if user_data and check_password_hash(user_data['password_hash'], password):
            user_obj = load_user(user_data['id'])
            login_user(user_obj)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('admin/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html', user=current_user)

# --- ADMIN: USERS ---
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

# --- ADMIN: ROLES ---
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

@app.route('/admin/roles/update/<int:role_id>', methods=['POST'])
@login_required
@permission_required('roles', 'update')
def update_role(role_id):
    # Updated resources list to include 'approvals'
    resources = ['users', 'roles', 'issues', 'small_claims', 'statutes', 'approvals']
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

# --- ADMIN: ISSUES ---
@app.route('/admin/issues')
@login_required
def admin_issues():
    if not current_user.can('issues', 'read'):
        flash('Access denied', 'danger')
        return redirect(url_for('admin_dashboard'))
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = 10
    offset = (page - 1) * per_page
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    count_query = "SELECT COUNT(*) as total FROM issues WHERE name LIKE %s"
    search_param = f"%{search}%"
    cursor.execute(count_query, (search_param,))
    total_records = cursor.fetchone()['total']
    total_pages = math.ceil(total_records / per_page)
    query = "SELECT * FROM issues WHERE name LIKE %s ORDER BY name ASC LIMIT %s OFFSET %s"
    cursor.execute(query, (search_param, per_page, offset))
    issues = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/issues.html', issues=issues, page=page, total_pages=total_pages, search=search)

@app.route('/admin/issues/add', methods=['GET', 'POST'])
@login_required
@permission_required('issues', 'create')
def admin_issue_add():
    if request.method == 'POST':
        name = request.form['name']
        slug = request.form['slug']
        description = request.form['description']
        if not name or not slug:
            flash('Name and Slug are required.', 'danger')
            return redirect(url_for('admin_issue_add'))
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM issues WHERE slug = %s", (slug,))
        if cursor.fetchone():
            flash('Error: Slug must be unique.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('admin_issue_add'))
        try:
            cursor.execute(
                "INSERT INTO issues (name, slug, description, updated_by, updated_dt) VALUES (%s, %s, %s, %s, NOW())",
                (name, slug, description, current_user.username)
            )
            conn.commit()
            flash('Issue category added.', 'success')
            return redirect(url_for('admin_issues'))
        except Error as e:
            flash(f'Database Error: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
    return render_template('admin/issue_form.html', action='Add')

@app.route('/admin/issues/edit/<int:issue_id>', methods=['GET', 'POST'])
@login_required
@permission_required('issues', 'update')
def admin_issue_edit(issue_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        name = request.form['name']
        slug = request.form['slug']
        description = request.form['description']
        cursor.execute("SELECT id FROM issues WHERE slug = %s AND id != %s", (slug, issue_id))
        if cursor.fetchone():
            flash('Error: Slug is already taken by another issue.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('admin_issue_edit', issue_id=issue_id))
        try:
            cursor.execute(
                "UPDATE issues SET name=%s, slug=%s, description=%s, updated_by=%s, updated_dt=NOW() WHERE id=%s",
                (name, slug, description, current_user.username, issue_id)
            )
            conn.commit()
            flash('Issue updated successfully.', 'success')
            return redirect(url_for('admin_issues'))
        except Error as e:
            flash(f'Database Error: {e}', 'danger')
    cursor.execute("SELECT * FROM issues WHERE id = %s", (issue_id,))
    issue = cursor.fetchone()
    cursor.close()
    conn.close()
    if not issue:
        flash('Issue not found', 'danger')
        return redirect(url_for('admin_issues'))
    return render_template('admin/issue_form.html', action='Edit', issue=issue)

@app.route('/admin/issues/delete/<int:issue_id>', methods=['GET'])
@login_required
@permission_required('issues', 'delete')
def admin_issue_delete(issue_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM issues WHERE id = %s", (issue_id,))
        conn.commit()
        flash('Issue deleted.', 'success')
    except Error as e:
        flash(f'Cannot delete issue: It may be linked to existing statutes.', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_issues'))

# --- ADMIN: SMALL CLAIMS (Modified for Approval Workflow) ---
@app.route('/admin/small_claims')
@login_required
def admin_small_claims():
    if not current_user.can('small_claims', 'read'):
        flash('Access denied', 'danger')
        return redirect(url_for('admin_dashboard'))
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = 10
    offset = (page - 1) * per_page
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    count_sql = "SELECT COUNT(*) as total FROM small_claims sc JOIN states s ON sc.state_id = s.id WHERE s.name LIKE %s"
    search_param = f"%{search}%"
    cursor.execute(count_sql, (search_param,))
    total_records = cursor.fetchone()['total']
    total_pages = math.ceil(total_records / per_page)
    sql = "SELECT sc.*, s.name as state_name FROM small_claims sc JOIN states s ON sc.state_id = s.id WHERE s.name LIKE %s ORDER BY s.name ASC LIMIT %s OFFSET %s"
    cursor.execute(sql, (search_param, per_page, offset))
    claims = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/small_claims.html', claims=claims, page=page, total_pages=total_pages, search=search)

@app.route('/admin/small_claims/add', methods=['GET', 'POST'])
@login_required
@permission_required('small_claims', 'create')
def admin_small_claims_add():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        state_id = request.form['state_id']
        small_claims_cap = request.form['small_claims_cap']
        small_claims_info = request.form['small_claims_info']
        if not state_id:
            flash('State is required.', 'danger')
            return redirect(url_for('admin_small_claims_add'))
        try:
            # Check pending queue too? For now just checking live.
            cursor.execute("SELECT id FROM small_claims WHERE state_id = %s", (state_id,))
            if cursor.fetchone():
                flash('Error: Small claims data already exists for this state.', 'danger')
            else:
                # CHANGED: Insert into approvals queue instead of live table
                cursor.execute(
                    """INSERT INTO small_claims_approvals 
                       (state_id, small_claims_cap, small_claims_info, action_type, status, submitted_by) 
                       VALUES (%s, %s, %s, 'INSERT', 'PENDING', %s)""",
                    (state_id, small_claims_cap, small_claims_info, current_user.username)
                )
                conn.commit()
                flash('Change submitted for approval.', 'info')
                cursor.close()
                conn.close()
                return redirect(url_for('admin_small_claims'))
        except Error as e:
            flash(f'Database Error: {e}', 'danger')
    cursor.execute("SELECT id, name FROM states ORDER BY name ASC")
    states = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/small_claims_form.html', action='Add', states=states)

@app.route('/admin/small_claims/edit/<int:claim_id>', methods=['GET', 'POST'])
@login_required
@permission_required('small_claims', 'update')
def admin_small_claims_edit(claim_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        state_id = request.form['state_id']
        small_claims_cap = request.form['small_claims_cap']
        small_claims_info = request.form['small_claims_info']
        try:
            # CHANGED: Insert into approvals queue with action_type='UPDATE'
            cursor.execute(
                """INSERT INTO small_claims_approvals 
                   (claim_id, state_id, small_claims_cap, small_claims_info, action_type, status, submitted_by) 
                   VALUES (%s, %s, %s, %s, 'UPDATE', 'PENDING', %s)""",
                (claim_id, state_id, small_claims_cap, small_claims_info, current_user.username)
            )
            conn.commit()
            flash('Update submitted for approval.', 'info')
            cursor.close()
            conn.close()
            return redirect(url_for('admin_small_claims'))
        except Error as e:
            flash(f'Database Error: {e}', 'danger')
            
    cursor.execute("SELECT * FROM small_claims WHERE id = %s", (claim_id,))
    claim = cursor.fetchone()
    cursor.execute("SELECT id, name FROM states ORDER BY name ASC")
    states = cursor.fetchall()
    cursor.close()
    conn.close()
    if not claim:
        flash('Record not found', 'danger')
        return redirect(url_for('admin_small_claims'))
    return render_template('admin/small_claims_form.html', action='Edit', claim=claim, states=states)

@app.route('/admin/small_claims/delete/<int:claim_id>', methods=['GET'])
@login_required
@permission_required('small_claims', 'delete')
def admin_small_claims_delete(claim_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # Need dict cursor to fetch existing data first
    try:
        # Fetch current data to preserve state_id in queue for reference
        cursor.execute("SELECT state_id FROM small_claims WHERE id = %s", (claim_id,))
        current_data = cursor.fetchone()
        
        if current_data:
            # CHANGED: Insert into approvals queue with action_type='DELETE'
            cursor.execute(
                """INSERT INTO small_claims_approvals 
                   (claim_id, state_id, action_type, status, submitted_by) 
                   VALUES (%s, %s, 'DELETE', 'PENDING', %s)""",
                (claim_id, current_data['state_id'], current_user.username)
            )
            conn.commit()
            flash('Deletion request submitted for approval.', 'info')
        else:
            flash('Record not found.', 'danger')
            
    except Error as e:
        flash(f'Error requesting deletion: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_small_claims'))

# --- ADMIN: APPROVALS QUEUE ---

@app.route('/admin/approvals/small_claims')
@login_required
def admin_small_claims_approvals():
    if not current_user.can('approvals', 'read'):
        flash('Access denied', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = 10
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Count pending
    count_sql = """
        SELECT COUNT(*) as total 
        FROM small_claims_approvals sca 
        JOIN states s ON sca.state_id = s.id 
        WHERE sca.status = 'PENDING' AND s.name LIKE %s
    """
    search_param = f"%{search}%"
    cursor.execute(count_sql, (search_param,))
    total_records = cursor.fetchone()['total']
    total_pages = math.ceil(total_records / per_page)
    
    # Fetch pending
    sql = """
        SELECT sca.*, s.name as state_name 
        FROM small_claims_approvals sca 
        JOIN states s ON sca.state_id = s.id 
        WHERE sca.status = 'PENDING' AND s.name LIKE %s 
        ORDER BY sca.submitted_dt DESC 
        LIMIT %s OFFSET %s
    """
    cursor.execute(sql, (search_param, per_page, offset))
    approvals = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/small_claims_approvals.html', 
                           approvals=approvals, 
                           page=page, 
                           total_pages=total_pages, 
                           search=search)

@app.route('/admin/approvals/small_claims/approve/<int:approval_id>')
@login_required
@permission_required('approvals', 'update')
def admin_small_claims_approve(approval_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Fetch the approval record
        cursor.execute("SELECT * FROM small_claims_approvals WHERE id = %s", (approval_id,))
        approval = cursor.fetchone()
        
        if not approval or approval['status'] != 'PENDING':
            flash('Invalid approval request.', 'danger')
            return redirect(url_for('admin_small_claims_approvals'))
            
        # Execute the change based on action_type
        if approval['action_type'] == 'INSERT':
            cursor.execute(
                """INSERT INTO small_claims (state_id, small_claims_cap, small_claims_info, updated_by, updated_dt) 
                   VALUES (%s, %s, %s, %s, NOW())""",
                (approval['state_id'], approval['small_claims_cap'], approval['small_claims_info'], approval['submitted_by'])
            )
        
        elif approval['action_type'] == 'UPDATE':
            cursor.execute(
                """UPDATE small_claims 
                   SET state_id=%s, small_claims_cap=%s, small_claims_info=%s, updated_by=%s, updated_dt=NOW() 
                   WHERE id=%s""",
                (approval['state_id'], approval['small_claims_cap'], approval['small_claims_info'], approval['submitted_by'], approval['claim_id'])
            )
            
        elif approval['action_type'] == 'DELETE':
            cursor.execute("DELETE FROM small_claims WHERE id = %s", (approval['claim_id'],))
            
        # Mark approval as done
        cursor.execute("UPDATE small_claims_approvals SET status='APPROVED' WHERE id = %s", (approval_id,))
        
        conn.commit()
        flash(f"Change ({approval['action_type']}) approved successfully.", 'success')
        
    except Error as e:
        flash(f'Database Error during approval: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('admin_small_claims_approvals'))

@app.route('/admin/approvals/small_claims/reject/<int:approval_id>')
@login_required
@permission_required('approvals', 'update')
def admin_small_claims_reject(approval_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE small_claims_approvals SET status='REJECTED' WHERE id = %s", (approval_id,))
        conn.commit()
        flash('Change request rejected.', 'warning')
    except Error as e:
        flash(f'Database Error: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('admin_small_claims_approvals'))

# --- ADMIN: STATUTES ---

@app.route('/admin/statutes')
@login_required
def admin_statutes():
    if not current_user.can('statutes', 'read'):
        flash('Access denied', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    state_filter = request.args.get('state_filter', '')
    issue_filter = request.args.get('issue_filter', '')
    
    per_page = 15
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Fetch dropdown filters
    cursor.execute("SELECT id, name FROM states ORDER BY name ASC")
    all_states = cursor.fetchall()
    cursor.execute("SELECT id, name FROM issues ORDER BY name ASC")
    all_issues = cursor.fetchall()
    
    # 2. Build Query
    conditions = []
    params = []
    
    if search:
        conditions.append("(s.name LIKE %s OR i.name LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
    if state_filter:
        conditions.append("st.state_id = %s")
        params.append(state_filter)
    if issue_filter:
        conditions.append("st.issue_id = %s")
        params.append(issue_filter)
        
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    # Count Query
    count_sql = f"""
        SELECT COUNT(*) as total 
        FROM statutes st
        JOIN states s ON st.state_id = s.id
        JOIN issues i ON st.issue_id = i.id
        {where_clause}
    """
    cursor.execute(count_sql, tuple(params))
    total_records = cursor.fetchone()['total']
    total_pages = math.ceil(total_records / per_page)
    
    # Data Query
    sql = f"""
        SELECT st.*, s.name as state_name, i.name as issue_name
        FROM statutes st
        JOIN states s ON st.state_id = s.id
        JOIN issues i ON st.issue_id = i.id
        {where_clause}
        ORDER BY s.name ASC, i.name ASC
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, offset])
    cursor.execute(sql, tuple(params))
    statutes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/statutes.html', 
                           statutes=statutes, 
                           page=page, 
                           total_pages=total_pages, 
                           search=search,
                           state_filter=state_filter,
                           issue_filter=issue_filter,
                           all_states=all_states,
                           all_issues=all_issues)

@app.route('/admin/statutes/add', methods=['GET', 'POST'])
@login_required
@permission_required('statutes', 'create')
def admin_statute_add():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Extract fields
        state_id = request.form.get('state_id')
        issue_id = request.form.get('issue_id')
        issue_info = request.form.get('issue_info')
        time_limit_type = request.form.get('time_limit_type')
        
        # Handle logic for Exact vs Range limits
        if time_limit_type == 'exact':
            limit_val = request.form.get('time_limit_max') 
            time_limit_min = limit_val
            time_limit_max = limit_val
        else:
            time_limit_min = request.form.get('time_limit_min')
            time_limit_max = request.form.get('time_limit_max')

        duration = request.form.get('duration')
        details = request.form.get('details')
        code_reference = request.form.get('code_reference')
        official_source_url = request.form.get('official_source_url')
        other_source_url = request.form.get('other_source_url')
        conditions_exceptions = request.form.get('conditions_exceptions')
        examples = request.form.get('examples')
        
        # Simple Validation
        if not state_id or not issue_id or not time_limit_min:
            flash('State, Issue, and Time Limit are required.', 'danger')
        else:
            try:
                # Check Duplicate
                cursor.execute("SELECT id FROM statutes WHERE state_id=%s AND issue_id=%s", (state_id, issue_id))
                if cursor.fetchone():
                    flash('Error: A statute for this state and issue already exists.', 'danger')
                else:
                    cursor.execute("""
                        INSERT INTO statutes (
                            state_id, issue_id, issue_info, time_limit_type, time_limit_min, time_limit_max, duration,
                            details, code_reference, official_source_url, other_source_url, conditions_exceptions, examples,
                            updated_by, updated_dt
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (state_id, issue_id, issue_info, time_limit_type, time_limit_min, time_limit_max, duration,
                          details, code_reference, official_source_url, other_source_url, conditions_exceptions, examples,
                          current_user.username))
                    conn.commit()
                    flash('Statute added successfully.', 'success')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('admin_statutes'))
            except Error as e:
                flash(f'Database Error: {e}', 'danger')

    # GET: Dropdown data
    cursor.execute("SELECT id, name FROM states ORDER BY name ASC")
    states = cursor.fetchall()
    cursor.execute("SELECT id, name FROM issues ORDER BY name ASC")
    issues = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin/statute_form.html', action='Add', states=states, issues=issues)

@app.route('/admin/statutes/edit/<int:statute_id>', methods=['GET', 'POST'])
@login_required
@permission_required('statutes', 'update')
def admin_statute_edit(statute_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        state_id = request.form.get('state_id')
        issue_id = request.form.get('issue_id')
        issue_info = request.form.get('issue_info')
        time_limit_type = request.form.get('time_limit_type')
        
        if time_limit_type == 'exact':
            limit_val = request.form.get('time_limit_max')
            time_limit_min = limit_val
            time_limit_max = limit_val
        else:
            time_limit_min = request.form.get('time_limit_min')
            time_limit_max = request.form.get('time_limit_max')
            
        duration = request.form.get('duration')
        details = request.form.get('details')
        code_reference = request.form.get('code_reference')
        official_source_url = request.form.get('official_source_url')
        other_source_url = request.form.get('other_source_url')
        conditions_exceptions = request.form.get('conditions_exceptions')
        examples = request.form.get('examples')
        
        try:
            # Check Duplicate (excluding self)
            cursor.execute("SELECT id FROM statutes WHERE state_id=%s AND issue_id=%s AND id != %s", (state_id, issue_id, statute_id))
            if cursor.fetchone():
                flash('Error: A statute for this state and issue already exists.', 'danger')
            else:
                cursor.execute("""
                    UPDATE statutes SET 
                        state_id=%s, issue_id=%s, issue_info=%s, time_limit_type=%s, time_limit_min=%s, time_limit_max=%s, duration=%s,
                        details=%s, code_reference=%s, official_source_url=%s, other_source_url=%s, conditions_exceptions=%s, examples=%s,
                        updated_by=%s, updated_dt=NOW()
                    WHERE id=%s
                """, (state_id, issue_id, issue_info, time_limit_type, time_limit_min, time_limit_max, duration,
                      details, code_reference, official_source_url, other_source_url, conditions_exceptions, examples,
                      current_user.username, statute_id))
                conn.commit()
                flash('Statute updated successfully.', 'success')
                cursor.close()
                conn.close()
                return redirect(url_for('admin_statutes'))
        except Error as e:
            flash(f'Database Error: {e}', 'danger')
            
    # GET Data
    cursor.execute("SELECT * FROM statutes WHERE id=%s", (statute_id,))
    statute = cursor.fetchone()
    
    cursor.execute("SELECT id, name FROM states ORDER BY name ASC")
    states = cursor.fetchall()
    cursor.execute("SELECT id, name FROM issues ORDER BY name ASC")
    issues = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not statute:
        flash('Statute not found', 'danger')
        return redirect(url_for('admin_statutes'))
        
    return render_template('admin/statute_form.html', action='Edit', statute=statute, states=states, issues=issues)

@app.route('/admin/statutes/delete/<int:statute_id>', methods=['GET'])
@login_required
@permission_required('statutes', 'delete')
def admin_statute_delete(statute_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM statutes WHERE id = %s", (statute_id,))
        conn.commit()
        flash('Statute deleted.', 'success')
    except Error as e:
        flash(f'Error deleting record: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_statutes'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)