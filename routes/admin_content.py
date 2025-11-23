import math
import pandas as pd
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from mysql.connector import Error
from db import get_db_connection
from auth_utils import permission_required

def register(app):
    # --- ISSUES ---
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
            issue_group = request.form['issue_group'] 
            
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
                    "INSERT INTO issues (name, slug, description, issue_group, updated_by, updated_dt) VALUES (%s, %s, %s, %s, %s, NOW())",
                    (name, slug, description, issue_group, current_user.username)
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
            issue_group = request.form['issue_group'] 
            
            cursor.execute("SELECT id FROM issues WHERE slug = %s AND id != %s", (slug, issue_id))
            if cursor.fetchone():
                flash('Error: Slug is already taken by another issue.', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('admin_issue_edit', issue_id=issue_id))
            try:
                cursor.execute(
                    "UPDATE issues SET name=%s, slug=%s, description=%s, issue_group=%s, updated_by=%s, updated_dt=NOW() WHERE id=%s",
                    (name, slug, description, issue_group, current_user.username, issue_id)
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

    # --- SMALL CLAIMS ---
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
                cursor.execute("SELECT id FROM small_claims WHERE state_id = %s", (state_id,))
                if cursor.fetchone():
                    flash('Error: Small claims data already exists for this state.', 'danger')
                else:
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
        cursor = conn.cursor(dictionary=True) 
        try:
            cursor.execute("SELECT state_id FROM small_claims WHERE id = %s", (claim_id,))
            current_data = cursor.fetchone()
            
            if current_data:
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

    # --- STATUTES ---
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
        
        cursor.execute("SELECT id, name FROM states ORDER BY name ASC")
        all_states = cursor.fetchall()
        cursor.execute("SELECT id, name FROM issues ORDER BY name ASC")
        all_issues = cursor.fetchall()
        
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

    @app.route('/admin/statutes/upload', methods=['POST'])
    @login_required
    @permission_required('statutes', 'create')
    def admin_statutes_upload():
        file = request.files.get('file')
        if not file or not file.filename:
            flash('No file selected', 'danger')
            return redirect(url_for('admin_statutes'))

        try:
            df = pd.read_excel(file)
            df.columns = [c.lower().strip() for c in df.columns]
        except Exception as e:
            flash(f'Error reading file: {e}', 'danger')
            return redirect(url_for('admin_statutes'))

        upload_limit = current_app.config.get('UPLOAD_ROW_LIMIT', 50)
        if len(df) > upload_limit:
            flash(f'Upload failed: Exceeds row limit of {upload_limit}.', 'danger')
            return redirect(url_for('admin_statutes'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch Mappings
        cursor.execute("SELECT id, name FROM states")
        state_map = {row['name'].lower(): row['id'] for row in cursor.fetchall()}
        
        cursor.execute("SELECT id, name FROM issues")
        issue_map = {row['name'].lower(): row['id'] for row in cursor.fetchall()}

        new_count, updated_count, failed_count = 0, 0, 0
        failed_rows = []

        valid_types = ['exact', 'range', 'conditional']
        valid_durations = ['years', 'months', 'days']

        for index, row in df.iterrows():
            state_name = str(row.get('state', '')).strip()
            issue_name = str(row.get('issue', '')).strip()
            
            # Validation 1: Mappings
            state_id = state_map.get(state_name.lower())
            issue_id = issue_map.get(issue_name.lower())
            
            if not state_id or not issue_id:
                failed_count += 1
                failed_rows.append(f"{state_name} / {issue_name} (Invalid State or Issue)")
                continue

            # Validation 2: Types & Durations
            time_limit_type = str(row.get('time limit type', 'exact')).strip().lower()
            duration = str(row.get('duration', 'years')).strip().lower()

            if time_limit_type not in valid_types:
                failed_count += 1
                failed_rows.append(f"{state_name} / {issue_name} (Invalid Type: {time_limit_type})")
                continue
            if duration not in valid_durations:
                failed_count += 1
                failed_rows.append(f"{state_name} / {issue_name} (Invalid Duration: {duration})")
                continue

            # Validation 3: Logic Checks
            min_time = row.get('min time')
            max_time = row.get('max time')
            
            # Ensure numeric safety
            try:
                min_val = int(float(min_time)) if pd.notna(min_time) else None
                max_val = int(float(max_time)) if pd.notna(max_time) else None
            except (ValueError, TypeError):
                failed_count += 1
                failed_rows.append(f"{state_name} / {issue_name} (Numeric Error)")
                continue

            if time_limit_type == 'exact' and max_val is not None:
                failed_count += 1
                failed_rows.append(f"{state_name} / {issue_name} (Exact type cannot have Max Time)")
                continue
            
            if time_limit_type in ['range', 'conditional']:
                if min_val is None or max_val is None:
                    failed_count += 1
                    failed_rows.append(f"{state_name} / {issue_name} (Range/Conditional needs both Min and Max)")
                    continue

            # Handle 'Exact' logic for DB storage (Min is used as primary value usually, or handle based on schema preference)
            # If exact, usually min_time holds the value, max can be same or null. 
            # Logic in add_statute form sets both to same value. Let's mirror that for consistency if needed,
            # or strictly follow schema. Schema has both.
            if time_limit_type == 'exact':
                # If exact, ensure min_val is set
                if min_val is None: 
                    failed_count += 1
                    failed_rows.append(f"{state_name} / {issue_name} (Exact requires Min Time)")
                    continue
                max_val = min_val # Normalize for DB if schema expects it, or leave None if allowed.
                                  # Current manual add sets both. Let's set both.

            # Check Existing
            cursor.execute("SELECT id FROM statutes WHERE state_id = %s AND issue_id = %s", (state_id, issue_id))
            existing = cursor.fetchone()
            
            action_type = 'UPDATE' if existing else 'INSERT'
            statute_id = existing['id'] if existing else None

            # Insert Approval
            try:
                sql = """
                    INSERT INTO statute_approvals (
                        statute_id, state_id, issue_id, issue_info, time_limit_type, 
                        time_limit_min, time_limit_max, duration, details, code_reference, 
                        official_source_url, other_source_url, conditions_exceptions, 
                        examples, tolling, action_type, status, submitted_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'PENDING', %s)
                """
                params = (
                    statute_id, state_id, issue_id, 
                    str(row.get('issue info', '')), time_limit_type, min_val, max_val, duration,
                    str(row.get('details', '')), str(row.get('code reference', '')),
                    str(row.get('official url', '')), str(row.get('other url', '')),
                    str(row.get('exceptions', '')), str(row.get('examples', '')),
                    str(row.get('tolling', '')), action_type, current_user.username
                )
                cursor.execute(sql, params)
                
                if action_type == 'UPDATE': updated_count += 1
                else: new_count += 1
                
            except Error as e:
                failed_count += 1
                failed_rows.append(f"{state_name} / {issue_name} (DB Error: {e})")

        conn.commit()
        cursor.close()
        conn.close()

        flash(f"Upload Complete. New: {new_count}, Updated: {updated_count}, Failed: {failed_count}", 'info')
        if failed_rows:
            flash(f"Failed Rows: {', '.join(failed_rows[:10])}...", 'warning')

        return redirect(url_for('admin_statutes'))

    @app.route('/admin/statutes/add', methods=['GET', 'POST'])
    @login_required
    @permission_required('statutes', 'create')
    def admin_statute_add():
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
            tolling = request.form.get('tolling')

            if not state_id or not issue_id or not time_limit_min:
                flash('State, Issue, and Time Limit are required.', 'danger')
            else:
                try:
                    cursor.execute("SELECT id FROM statutes WHERE state_id=%s AND issue_id=%s", (state_id, issue_id))
                    if cursor.fetchone():
                        flash('Error: A statute for this state and issue already exists.', 'danger')
                    else:
                        cursor.execute("""
                            INSERT INTO statute_approvals (
                                state_id, issue_id, issue_info, time_limit_type, time_limit_min, time_limit_max, duration,
                                details, code_reference, official_source_url, other_source_url, conditions_exceptions, examples, tolling,
                                action_type, status, submitted_by
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'INSERT', 'PENDING', %s)
                        """, (state_id, issue_id, issue_info, time_limit_type, time_limit_min, time_limit_max, duration,
                              details, code_reference, official_source_url, other_source_url, conditions_exceptions, examples, tolling,
                              current_user.username))
                        conn.commit()
                        flash('Statute creation submitted for approval.', 'info')
                        cursor.close()
                        conn.close()
                        return redirect(url_for('admin_statutes'))
                except Error as e:
                    flash(f'Database Error: {e}', 'danger')

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
            tolling = request.form.get('tolling')

            try:
                cursor.execute("SELECT id FROM statutes WHERE state_id=%s AND issue_id=%s AND id != %s", (state_id, issue_id, statute_id))
                if cursor.fetchone():
                    flash('Error: A statute for this state and issue already exists.', 'danger')
                else:
                    cursor.execute("""
                        INSERT INTO statute_approvals (
                            statute_id, state_id, issue_id, issue_info, time_limit_type, time_limit_min, time_limit_max, duration,
                            details, code_reference, official_source_url, other_source_url, conditions_exceptions, examples, tolling,
                            action_type, status, submitted_by
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'UPDATE', 'PENDING', %s)
                    """, (statute_id, state_id, issue_id, issue_info, time_limit_type, time_limit_min, time_limit_max, duration,
                          details, code_reference, official_source_url, other_source_url, conditions_exceptions, examples, tolling,
                          current_user.username))
                    conn.commit()
                    flash('Statute update submitted for approval.', 'info')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('admin_statutes'))
            except Error as e:
                flash(f'Database Error: {e}', 'danger')
                
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
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM statutes WHERE id = %s", (statute_id,))
            s = cursor.fetchone()
            
            if s:
                cursor.execute("""
                    INSERT INTO statute_approvals (
                        statute_id, state_id, issue_id, 
                        action_type, status, submitted_by
                    ) VALUES (%s, %s, %s, 'DELETE', 'PENDING', %s)
                """, (statute_id, s['state_id'], s['issue_id'], current_user.username))
                
                conn.commit()
                flash('Statute deletion request submitted for approval.', 'info')
            else:
                flash('Record not found.', 'danger')
                
        except Error as e:
            flash(f'Error requesting deletion: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('admin_statutes'))
        
    # --- ISSUE REPORTS ---
    @app.route('/admin/reports')
    @login_required
    def admin_reports():
        # Uses 'statutes' 'read' permission as proxy for viewing reports
        if not current_user.can('statutes', 'read'):
            flash('Access denied', 'danger')
            return redirect(url_for('admin_dashboard'))
            
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'all') # all, pending, valid, invalid
        
        per_page = 20
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        conditions = []
        params = []
        
        if status_filter == 'pending':
            conditions.append("is_valid IS NULL")
        elif status_filter == 'valid':
            conditions.append("is_valid = 1")
        elif status_filter == 'invalid':
            conditions.append("is_valid = 0")
            
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Count
        count_sql = f"SELECT COUNT(*) as total FROM issue_reports {where_clause}"
        cursor.execute(count_sql, tuple(params))
        total_records = cursor.fetchone()['total']
        total_pages = math.ceil(total_records / per_page)
        
        # Fetch
        sql = f"SELECT * FROM issue_reports {where_clause} ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        cursor.execute(sql, tuple(params))
        reports = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/reports.html', reports=reports, page=page, total_pages=total_pages, status_filter=status_filter)

    @app.route('/admin/reports/validate/<int:report_id>/<int:is_valid>')
    @login_required
    def admin_report_validate(report_id, is_valid):
        # Uses 'statutes' 'update' permission to validate
        if not current_user.can('statutes', 'update'):
            flash('Access denied', 'danger')
            return redirect(url_for('admin_reports'))
            
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            val = 1 if is_valid else 0
            cursor.execute("UPDATE issue_reports SET is_valid = %s WHERE id = %s", (val, report_id))
            conn.commit()
            status_msg = "marked as Valid" if val else "marked as Invalid"
            flash(f'Report {status_msg}.', 'success')
        except Error as e:
            flash(f'Database Error: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
            
        return redirect(url_for('admin_reports'))