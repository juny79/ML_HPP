from flask import Blueprint, jsonify

leaderboard_bp = Blueprint('leaderboard', __name__)


@leaderboard_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    # Placeholder: integrate DB query to return top submissions
    return jsonify([])
