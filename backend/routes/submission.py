from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename

from ..services.file_handler import save_upload
from ..services.evaluator import evaluate_submission

submission_bp = Blueprint('submission', __name__)


@submission_bp.route('/submit', methods=['POST'])
def submit():
    if 'file' not in request.files:
        return jsonify({'error': 'no file provided'}), 400
    file = request.files['file']
    username = request.form.get('username', 'anonymous')

    filename = save_upload(file)
    score = evaluate_submission(filename, username)

    return jsonify({'username': username, 'score': score, 'filename': os.path.basename(filename)})
