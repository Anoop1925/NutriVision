from flask import Blueprint, render_template, session

pages_bp = Blueprint('pages', __name__)


def _ctx():
    """Common template context."""
    user = session.get('user')
    return {'user': user, 'logged_in': user is not None}


@pages_bp.route('/')
def index():
    return render_template('index.html', **_ctx(), active='home')


@pages_bp.route('/login')
def login():
    return render_template('login.html', **_ctx())


@pages_bp.route('/diet')
def diet():
    return render_template('diet.html', **_ctx(), active='diet')


@pages_bp.route('/recipes')
def recipes():
    return render_template('recipes.html', **_ctx(), active='recipes')


@pages_bp.route('/analyzer')
def analyzer():
    return render_template('analyzer.html', **_ctx(), active='analyzer')

