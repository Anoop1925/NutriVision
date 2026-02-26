"""
Demo authentication — no database, hard-coded credentials.
"""
from flask import Blueprint, request, jsonify, session, redirect, url_for

auth_bp = Blueprint('auth', __name__)

# Demo credentials
DEMO_USERS = {
    'demo@nutrivision.ai': 'demo1234',
    'admin@nutrivision.ai': 'admin1234',
}


@auth_bp.route('/login', methods=['POST'])
def login():
    d = request.get_json(force=True)
    email = d.get('email', '').strip().lower()
    password = d.get('password', '')

    if email in DEMO_USERS and DEMO_USERS[email] == password:
        session['user'] = {
            'email': email,
            'name': email.split('@')[0].title(),
            'avatar': email[0].upper(),
        }
        return jsonify({'ok': True, 'user': session['user']})

    return jsonify({'ok': False, 'error': 'Invalid email or password'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'ok': True})


@auth_bp.route('/me')
def me():
    user = session.get('user')
    if user:
        return jsonify({'authenticated': True, 'user': user})
    return jsonify({'authenticated': False}), 401
