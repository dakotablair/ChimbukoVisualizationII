import os
from flask import Flask
from config import config

# Flask extensions
# (e.g.) SQLAlchemy


# Import models if there is (for SQLAlchemy)


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('SERVER_CONFIG', 'development')
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize flask extensions
    # (e.g. database)

    # Register web application routes
    from .server import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Register API routes
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
