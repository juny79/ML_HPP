import os
from werkzeug.utils import secure_filename


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def save_upload(file):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    upload_dir = os.path.join(project_root, '..', 'uploads')
    ensure_dir(upload_dir)
    filename = secure_filename(file.filename)
    dest = os.path.join(upload_dir, filename)
    file.save(dest)
    return dest
