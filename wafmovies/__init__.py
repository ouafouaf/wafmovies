from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate 
from flask_sqlalchemy import SQLAlchemy 
from flask_bootstrap import Bootstrap


# Initialization

db = SQLAlchemy()
login_manager = LoginManager()

# Application factory

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_pyfile('config.py')

    Bootstrap(app)
    db.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_message = "You must be logged in to access this page."
    login_manager.login_view = "routes.login"

    migrate = Migrate(app, db)

    # Blueprints registration

    from .auth import auth as auth_bp
    app.register_blueprint(auth_bp)

    from .home import home as home_bp
    app.register_blueprint(home_bp)

    from .admin import admin as admin_bp
    app.register_blueprint(admin_bp)

    # Return app

    return app