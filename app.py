import datetime
from flask import Flask, render_template, request, abort, jsonify, Response
import mysql.connector
from mysql.connector import Error
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Database Connection Helper
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

# --- Context Processors ---
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.utcnow()}

# --- Routes ---

@app.route('/')
def index():
    """Homepage with Search Interface"""
    conn = get_db_connection()
    if not conn:
        return "Database Error", 500
    
    cursor = conn.cursor(dictionary=True)
    
    # Fetch dropdown options
    cursor.execute("SELECT name, slug FROM states ORDER BY name ASC")
    states = cursor.fetchall()
    
    cursor.execute("SELECT name, slug FROM issues ORDER BY name ASC")
    issues = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('home.html', states=states, issues=issues)

@app.route('/limitations/<state_slug>/<issue_slug>')
def statute_detail(state_slug, issue_slug):
    """Programmatic SEO Landing Page"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch Main Statute Data
    query = """
        SELECT 
            s.name as state_name, 
            s.small_claims_cap,
            s.small_claims_info,
            i.name as issue_name,
            i.description as issue_desc,
            st.years, 
            st.code_reference, 
            st.details,
            st.last_updated
        FROM statutes st
        JOIN states s ON st.state_id = s.id
        JOIN issues i ON st.issue_id = i.id
        WHERE s.slug = %s AND i.slug = %s
    """
    cursor.execute(query, (state_slug, issue_slug))
    data = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not data:
        abort(404) # Clean 404 if combination doesn't exist
        
    return render_template('statute.html', data=data, state_slug=state_slug, issue_slug=issue_slug)

@app.route('/report-issue', methods=['POST'])
def report_issue():
    """Handle data correction reports via AJAX"""
    data = request.json
    # In production, use smtplib to send this data to admin email
    # using app.config['MAIL_USERNAME'] etc.
    
    print(f"ISSUE REPORTED: {data}") # Log for now
    
    return jsonify({'status': 'success', 'message': 'Report received. We will verify the data.'})

@app.route('/sitemap.xml')
def sitemap():
    """Dynamic Sitemap for Google SEO"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all valid combinations
    query = """
        SELECT s.slug as state_slug, i.slug as issue_slug, st.last_updated
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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)