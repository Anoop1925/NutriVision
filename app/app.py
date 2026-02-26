import sys, os

# Change working directory to the parent (foodai/) so that existing modules
# that do relative file reads (e.g. pd.read_csv('updated.csv')) work correctly.
_parent = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
os.chdir(_parent)
sys.path.insert(0, _parent)

from flask import Flask
from flask_cors import CORS
from routes.diet import diet_bp
from routes.custom import custom_bp
from routes.analyzer import analyzer_bp
from routes.pages import pages_bp
from routes.auth import auth_bp

def create_app():
    _app_dir = os.path.join(_parent, 'app')
    app = Flask(__name__,
                static_folder=os.path.join(_app_dir, 'static'),
                template_folder=os.path.join(_app_dir, 'templates'))
    app.secret_key = 'nutrivision-demo-secret-key-2026'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

    CORS(app)

    # Register blueprints
    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(diet_bp, url_prefix='/api/diet')
    app.register_blueprint(custom_bp, url_prefix='/api/custom')
    app.register_blueprint(analyzer_bp, url_prefix='/api/analyzer')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000, use_reloader=False)
