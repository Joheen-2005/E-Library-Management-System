"""
app.py — Flask application factory with error handlers.
Run: python app.py   OR   flask run
"""
import os
from flask import Flask, render_template
from flask_login import LoginManager
from config.config import config
from models.models import db, User


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth  import auth_bp
    from routes.main  import main_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('404.html'), 500

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, port=5000)
