import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from celery import Celery
from .provdb import ProvDB
from config import config

# Flask extensions
db = SQLAlchemy()
socketio = SocketIO()
pdb = ProvDB(pdb_path=os.environ.get('PROVENANCE_DB', ''),
             pdb_sharded_num=int(os.environ.get('SHARDED_NUM', 0)),
             pdb_addr=os.environ.get('PROVDB_ADDR', ''))
celery = Celery(__name__,
                broker=os.environ.get('CELERY_BROKER_URL', 'redis://'),
                backend=os.environ.get('CELERY_BROKER_URL', 'redis://'))
celery.config_from_object('celeryconfig')

# Import models so that they are registered with SQLAlchemy
from . import models  # noqa

# Import celery task so that it is registered with the Celery workers
from .tasks import run_flask_request  # noqa

# Import Socket.IO events so that they are registered with Flask-SocketIO
from . import events  # noqa


def create_app(config_name=None, main=True):
    if config_name is None:
        config_name = os.environ.get('SERVER_CONFIG', 'development')

    # print(config_name, config[config_name].SQLALCHEMY_BINDS)

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize flask extensions
    db.init_app(app)
    if main:
        # Initialize socketio server and attach it to the message queue, so
        # that everything works even when there are multiple servers or
        # additional processes such as Celery workers wanting to access
        # Socket.IO
        socketio.init_app(app,
                          message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'])
    else:
        # Initialize socketio to emit events through the message queue
        # Note that since Celery does not use eventlet, we have to be explicit
        # in setting the async mode to not use it.
        socketio.init_app(None,
                          message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'],
                          async_mode='threading')
    celery.conf.update(config[config_name].CELERY_CONFIG)

    # Register web application routes
    from .server import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Register API routes
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # Register async tasks support
    from .tasks import tasks_bp as tasks_blueprint
    app.register_blueprint(tasks_blueprint, url_prefix='/tasks')

    # Register events routes
    from .events import events as events_blueprint
    app.register_blueprint(events_blueprint, url_prefix='/events')

    return app
