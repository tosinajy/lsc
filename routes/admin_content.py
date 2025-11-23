import math
from flask import render_template, request, redirect, url_for, flash
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
            issue_group = request.form['issue_group'] # NEW
            
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
            issue_group = request.form['issue_group'] # NEW
            
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