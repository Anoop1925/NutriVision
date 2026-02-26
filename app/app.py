import sys, os, urllib.request

# Change working directory to the parent (foodai/) so that existing modules
# that do relative file reads (e.g. pd.read_csv('updated.csv')) work correctly.
_parent = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
os.chdir(_parent)
sys.path.insert(0, _parent)

# ── Auto-download updated.csv from GitHub LFS if missing (Railway / CI) ──────
_CSV_PATH = os.path.join(_parent, 'updated.csv')
_CSV_URL  = "https://media.githubusercontent.com/media/Anoop1925/NutriVision/master/updated.csv"

if not os.path.exists(_CSV_PATH):
    print(f"[startup] updated.csv not found — downloading from GitHub LFS …", flush=True)
    try:
        urllib.request.urlretrieve(_CSV_URL, _CSV_PATH)
        print(f"[startup] updated.csv downloaded ({os.path.getsize(_CSV_PATH)//1024//1024} MB)", flush=True)
    except Exception as e:
        print(f"[startup] WARNING: could not download updated.csv: {e}", flush=True)

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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', debug=False, port=port, use_reloader=False)
