from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_login import LoginManager
from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
admin = Admin(template_mode='bootstrap3')
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_name):
    """Create an application instance."""
    app = Flask(__name__)

    # apply configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # initialize extensions
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    admin.init_app(app)
    login_manager.init_app(app)

    # register blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app
