import os

import logging

from flask import Flask, jsonify

from flask_sqlalchemy import SQLAlchemy

from flask_jwt_extended import JWTManager

from flask_cors import CORS



from config import config

from models.database import db

from routes.auth import auth_bp

from routes.submission import submission_bp

from routes.leaderboard import leaderboard_bp



# 로깅 설정

logging.basicConfig(

    level   = logging.INFO,

    format  = '%(asctime)s [%(levelname)s] %(name)s: %(message)s',

    handlers=[

        logging.StreamHandler(),

        logging.FileHandler('app.log', encoding='utf-8')

    ]

)

logger = logging.getLogger(__name__)





def create_app(config_name: str = 'default') -> Flask:

    """Flask 앱 팩토리"""

    app = Flask(__name__)

    app.config.from_object(config[config_name])



    # 추가 설정

    app.config['GROUND_TRUTH_PATH'] = os.environ.get(

        'GROUND_TRUTH_PATH',

        'data/ground_truth.csv'

    )



    # 확장 초기화

    db.init_app(app)

    JWTManager(app)

    CORS(app, resources={r"/api/*": {"origins": "*"}})



    # Blueprint 등록

    app.register_blueprint(auth_bp,        url_prefix='/api/auth')

    app.register_blueprint(submission_bp,  url_prefix='/api')

    app.register_blueprint(leaderboard_bp, url_prefix='/api')



    # DB 테이블 생성

    with app.app_context():

        db.create_all()

        _create_admin_user(app)



    # 에러 핸들러 등록

    _register_error_handlers(app)



    logger.info("Flask 앱 초기화 완료")

    return app





def _create_admin_user(app: Flask):

    """초기 관리자 계정 생성"""

    from models.database import User



    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')

    admin_email    = os.environ.get('ADMIN_EMAIL',    'admin@competition.com')

    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin1234!')



    existing = User.query.filter_by(username=admin_username).first()

    if not existing:

        admin = User(

            username  = admin_username,

            email     = admin_email,

            team_name = 'Admin',

            is_admin  = True

        )

        admin.set_password(admin_password)

        db.session.add(admin)

        db.session.commit()

        logger.info(f"관리자 계정 생성 완료: {admin_username}")





def _register_error_handlers(app: Flask):

    """전역 에러 핸들러"""



    @app.errorhandler(400)

    def bad_request(e):

        return jsonify({'success': False, 'message': '잘못된 요청입니다.'}), 400



    @app.errorhandler(401)

    def unauthorized(e):

        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401



    @app.errorhandler(403)

    def forbidden(e):

        return jsonify({'success': False, 'message': '접근 권한이 없습니다.'}), 403



    @app.errorhandler(404)

    def not_found(e):

        return jsonify({'success': False, 'message': '리소스를 찾을 수 없습니다.'}), 404



    @app.errorhandler(413)

    def file_too_large(e):

        return jsonify({'success': False, 'message': '파일 크기가 너무 큽니다. (최대 16MB)'}), 413



    @app.errorhandler(429)

    def too_many_requests(e):

        return jsonify({'success': False, 'message': '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.'}), 429



    @app.errorhandler(500)

    def internal_error(e):

        logger.error(f"서버 내부 오류: {str(e)}")

        return jsonify({'success': False, 'message': '서버 내부 오류가 발생했습니다.'}), 500



    @app.route('/api/health', methods=['GET'])

    def health_check():

        """서버 상태 확인"""

        return jsonify({

            'success': True,

            'message': 'Server is running',

            'version': '1.0.0'

        })





if __name__ == '__main__':

    app = create_app(os.environ.get('FLASK_ENV', 'development'))

    app.run(

        host  = '0.0.0.0',

        port  = int(os.environ.get('PORT', 5000)),

        debug = app.config['DEBUG']

    )

