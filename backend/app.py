from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Register blueprints (import here to avoid circular imports)
    try:
        from routes.submission import submission_bp
        from routes.leaderboard import leaderboard_bp
        from routes.auth import auth_bp

        app.register_blueprint(submission_bp, url_prefix='/api')
        app.register_blueprint(leaderboard_bp, url_prefix='/api')
        app.register_blueprint(auth_bp, url_prefix='/api')
    except Exception:
        # Blueprints may not exist yet during initial scaffold
        pass

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
