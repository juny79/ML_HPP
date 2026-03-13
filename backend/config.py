import os
from datetime import timedelta

class Config:
    # 기본 설정
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'house-price-prediction-secret-key'
    
    # 데이터베이스 설정
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///leaderboard.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 파일 업로드 설정
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 제한
    ALLOWED_EXTENSIONS = {'csv'}
    
    # 대회 설정
    MAX_SUBMISSIONS_PER_DAY = 5           # 일일 최대 제출 횟수
    TOTAL_TEST_SAMPLES = 9272             # 테스트 샘플 수
    
    # JWT 설정
    JWT_EXPIRATION = timedelta(hours=24)
    
    # 리더보드 설정
    LEADERBOARD_PUBLIC_RATIO = 0.5        # Public 리더보드 비율 (50%)
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

