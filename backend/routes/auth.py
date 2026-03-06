from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', 'guest')
    # NOTE: This is a placeholder. Replace with real auth logic.
    return jsonify({'user': username, 'token': 'fake-token'})
