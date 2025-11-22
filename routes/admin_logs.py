import math
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import get_db_connection

def register(app):
    @app.route('/admin/logs/login')
    @login_required
    def admin_login_logs():
        # Basic Permission Check (using the 'logs' resource added to roles)
        if not current_user.can('logs', 'read'):
            flash('Access denied', 'danger')
            return redirect(url_for('admin_dashboard'))
            
        page = request.args.get('page', 1, type=int)
        search_username = request.args.get('username', '')
        filter_status = request.args.get('status', '')
        # Date Range parameters
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        per_page = 20
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Build Query
        conditions = []
        params = []
        
        if search_username:
            conditions.append("username_attempted LIKE %s")
            params.append(f"%{search_username}%")
        
        if filter_status:
            conditions.append("status = %s")
            params.append(filter_status)
            
        # Date Range Logic
        if start_date:
            conditions.append("DATE(login_dt) >= %s")
            params.append(start_date)
            
        if end_date:
            conditions.append("DATE(login_dt) <= %s")
            params.append(end_date)
            
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Count Total
        count_sql = f"SELECT COUNT(*) as total FROM login_logs {where_clause}"
        cursor.execute(count_sql, tuple(params))
        total_records = cursor.fetchone()['total']
        total_pages = math.ceil(total_records / per_page)
        
        # Fetch Logs
        sql = f"""
            SELECT * FROM login_logs 
            {where_clause} 
            ORDER BY login_dt DESC 
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, offset])
        cursor.execute(sql, tuple(params))
        logs = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/login_history.html', 
                               logs=logs, 
                               page=page, 
                               total_pages=total_pages,
                               search_username=search_username,
                               filter_status=filter_status,
                               start_date=start_date,
                               end_date=end_date)
