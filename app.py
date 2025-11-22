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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

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
