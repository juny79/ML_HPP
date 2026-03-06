import os

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
    DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
    GROUND_TRUTH = os.path.join(DATA_DIR, 'ground_truth.csv')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(DATA_DIR, 'db.sqlite')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')
