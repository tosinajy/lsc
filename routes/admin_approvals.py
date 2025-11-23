import math
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from mysql.connector import Error
from db import get_db_connection
from auth_utils import permission_required

def register(app):
    # --- SMALL CLAIMS APPROVALS ---
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

    @app.route('/admin/approvals/small_claims/view/<int:approval_id>')
    @login_required
    def admin_small_claims_approval_view(approval_id):
        if not current_user.can('approvals', 'read'):
            flash('Access denied', 'danger')
            return redirect(url_for('admin_dashboard'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT sca.*, s.name as state_name 
            FROM small_claims_approvals sca 
            JOIN states s ON sca.state_id = s.id 
            WHERE sca.id = %s
        """, (approval_id,))
        approval = cursor.fetchone()
        
        if not approval:
            cursor.close()
            conn.close()
            flash('Approval request not found', 'danger')
            return redirect(url_for('admin_small_claims_approvals'))
            
        current_record = None
        if approval['claim_id']:
            cursor.execute("SELECT * FROM small_claims WHERE id = %s", (approval['claim_id'],))
            current_record = cursor.fetchone()
            
        cursor.close()
        conn.close()
        
        return render_template('admin/small_claims_approval_view.html', 
                               approval=approval, 
                               current_record=current_record)

    @app.route('/admin/approvals/small_claims/approve/<int:approval_id>')
    @login_required
    @permission_required('approvals', 'update')
    def admin_small_claims_approve(approval_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT * FROM small_claims_approvals WHERE id = %s", (approval_id,))
            approval = cursor.fetchone()
            
            if not approval or approval['status'] != 'PENDING':
                flash('Invalid approval request.', 'danger')
                return redirect(url_for('admin_small_claims_approvals'))
                
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

    # --- STATUTE APPROVALS ---
    @app.route('/admin/approvals/statutes')
    @login_required
    def admin_statutes_approvals():
        if not current_user.can('approvals', 'read'):
            flash('Access denied', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        per_page = 10
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        count_sql = """
            SELECT COUNT(*) as total 
            FROM statute_approvals sa 
            JOIN states s ON sa.state_id = s.id 
            JOIN issues i ON sa.issue_id = i.id
            WHERE sa.status = 'PENDING' AND (s.name LIKE %s OR i.name LIKE %s)
        """
        search_param = f"%{search}%"
        cursor.execute(count_sql, (search_param, search_param))
        total_records = cursor.fetchone()['total']
        total_pages = math.ceil(total_records / per_page)
        
        sql = """
            SELECT sa.*, s.name as state_name, i.name as issue_name
            FROM statute_approvals sa 
            JOIN states s ON sa.state_id = s.id 
            JOIN issues i ON sa.issue_id = i.id
            WHERE sa.status = 'PENDING' AND (s.name LIKE %s OR i.name LIKE %s) 
            ORDER BY sa.submitted_dt DESC 
            LIMIT %s OFFSET %s
        """
        cursor.execute(sql, (search_param, search_param, per_page, offset))
        approvals = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/statute_approvals.html', 
                               approvals=approvals, 
                               page=page, 
                               total_pages=total_pages, 
                               search=search)

    @app.route('/admin/approvals/statutes/view/<int:approval_id>')
    @login_required
    def admin_statute_approval_view(approval_id):
        if not current_user.can('approvals', 'read'):
            flash('Access denied', 'danger')
            return redirect(url_for('admin_dashboard'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT sa.*, s.name as state_name, i.name as issue_name
            FROM statute_approvals sa 
            JOIN states s ON sa.state_id = s.id 
            JOIN issues i ON sa.issue_id = i.id
            WHERE sa.id = %s
        """, (approval_id,))
        approval = cursor.fetchone()
        
        if not approval:
            cursor.close()
            conn.close()
            flash('Approval request not found', 'danger')
            return redirect(url_for('admin_statutes_approvals'))
            
        current_record = None
        if approval['statute_id']:
            cursor.execute("""
                SELECT st.*, s.name as state_name, i.name as issue_name
                FROM statutes st
                JOIN states s ON st.state_id = s.id
                JOIN issues i ON st.issue_id = i.id
                WHERE st.id = %s
            """, (approval['statute_id'],))
            current_record = cursor.fetchone()
            
        cursor.close()
        conn.close()
        
        return render_template('admin/statute_approval_view.html', 
                               approval=approval, 
                               current_record=current_record)

    @app.route('/admin/approvals/statutes/approve/<int:approval_id>')
    @login_required
    @permission_required('approvals', 'update')
    def admin_statute_approve(approval_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT * FROM statute_approvals WHERE id = %s", (approval_id,))
            approval = cursor.fetchone()
            
            if not approval or approval['status'] != 'PENDING':
                flash('Invalid approval request.', 'danger')
                return redirect(url_for('admin_statutes_approvals'))
            
            if approval['action_type'] == 'INSERT':
                cursor.execute("""
                    INSERT INTO statutes (
                        state_id, issue_id, issue_info, time_limit_type, time_limit_min, time_limit_max, duration,
                        details, code_reference, official_source_url, other_source_url, conditions_exceptions, examples, tolling,
                        updated_by, updated_dt
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (approval['state_id'], approval['issue_id'], approval['issue_info'], approval['time_limit_type'], 
                      approval['time_limit_min'], approval['time_limit_max'], approval['duration'], approval['details'], 
                      approval['code_reference'], approval['official_source_url'], approval['other_source_url'], 
                      approval['conditions_exceptions'], approval['examples'], approval['tolling'], approval['submitted_by']))
            
            elif approval['action_type'] == 'UPDATE':
                cursor.execute("""
                    UPDATE statutes SET 
                        state_id=%s, issue_id=%s, issue_info=%s, time_limit_type=%s, time_limit_min=%s, time_limit_max=%s, duration=%s,
                        details=%s, code_reference=%s, official_source_url=%s, other_source_url=%s, conditions_exceptions=%s, examples=%s, tolling=%s,
                        updated_by=%s, updated_dt=NOW()
                    WHERE id=%s
                """, (approval['state_id'], approval['issue_id'], approval['issue_info'], approval['time_limit_type'], 
                      approval['time_limit_min'], approval['time_limit_max'], approval['duration'], approval['details'], 
                      approval['code_reference'], approval['official_source_url'], approval['other_source_url'], 
                      approval['conditions_exceptions'], approval['examples'], approval['tolling'], approval['submitted_by'], approval['statute_id']))
                
            elif approval['action_type'] == 'DELETE':
                cursor.execute("DELETE FROM statutes WHERE id = %s", (approval['statute_id'],))
                
            cursor.execute("UPDATE statute_approvals SET status='APPROVED' WHERE id = %s", (approval_id,))
            conn.commit()
            flash(f"Statute change ({approval['action_type']}) approved successfully.", 'success')
            
        except Error as e:
            flash(f'Database Error during approval: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
            
        return redirect(url_for('admin_statutes_approvals'))

    @app.route('/admin/approvals/statutes/reject/<int:approval_id>')
    @login_required
    @permission_required('approvals', 'update')
    def admin_statute_reject(approval_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE statute_approvals SET status='REJECTED' WHERE id = %s", (approval_id,))
            conn.commit()
            flash('Statute change request rejected.', 'warning')
        except Error as e:
            flash(f'Database Error: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
            
        return redirect(url_for('admin_statutes_approvals'))