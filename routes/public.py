from flask import render_template, request, jsonify, Response, abort
from mysql.connector import Error
from db import get_db_connection

def register(app):
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
        # 'last_updated' is now provided via app.context_processor in app.py
        return render_template('home.html', states=states)

    @app.route('/api/issues/<state_slug>')
    def get_issues_by_state(state_slug):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT DISTINCT i.id, i.name, i.slug, i.issue_group
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
                i.issue_group,
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
        details = data.get('details')
        email = data.get('email') # Re-added
        official_source = data.get('official_source')
        page_context = data.get('url')
        
        # Validation
        if not details:
            return jsonify({'status': 'error', 'message': 'Correction details are required.'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Re-added reporter_email to INSERT statement
            cursor.execute("""
                INSERT INTO issue_reports (details, reporter_email, official_source, page_context, is_valid, created_at)
                VALUES (%s, %s, %s, %s, NULL, NOW())
            """, (details, email, official_source, page_context))
            conn.commit()
            return jsonify({'status': 'success', 'message': 'Thank you. Your correction has been submitted for review.'})
        except Error as e:
            print(f"Database Error: {e}")
            return jsonify({'status': 'error', 'message': 'Failed to save report.'}), 500
        finally:
            cursor.close()
            conn.close()

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