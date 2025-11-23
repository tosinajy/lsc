import datetime
import json
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from auth_utils import AnonymousUser, load_user_from_db
import routes.public as public_routes
import routes.auth as auth_routes
import routes.admin_system as admin_system
import routes.admin_content as admin_content
import routes.admin_approvals as admin_approvals
import routes.admin_logs as admin_logs

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

@app.context_processor
def inject_globals():
    return {'now': datetime.datetime.utcnow()}

# --- Error Handlers ---
@app.errorhandler(404)
def page_not_found(e):
    # This catches all 404 errors (invalid URLs, or manual abort(404) calls)
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    # It's good practice to have a generic error page for 500s as well
    # For now, we can reuse the layout or a simple message
    return render_template('base.html', content="<div class='text-center py-5'><h1>500</h1><p>Internal Server Error. Please try again later.</p></div>"), 500

# --- Auth Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return load_user_from_db(user_id)

# --- Register Routes ---
public_routes.register(app)
auth_routes.register(app)
admin_system.register(app)
admin_content.register(app)
admin_approvals.register(app)
admin_logs.register(app)

if __name__ == '__main__':
    app.run(debug=True)