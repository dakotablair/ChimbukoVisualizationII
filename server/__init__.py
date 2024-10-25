# needed (?) for using redis in this configuration
# from gevent import monkey
# monkey.patch_all()

import os  # noqa: E402
from flask import Flask  # noqa: E402
from config import config  # noqa: E402

from .core import db, celery, pdb, socketio  # noqa: E402
from .datamodel import DataModel  # noqa: E402

# Flask extensions
dm = DataModel()
# Import Socket.IO events so that they are registered with Flask-SocketIO
from . import events  # noqa


def create_app(config_name=None, main=True):
    print("create_app call")
    if config_name is None:
        config_name = os.environ.get("SERVER_CONFIG", "development")

    # print(config_name, config[config_name].SQLALCHEMY_BINDS)
    print(f"config: {config_name} --- {config[config_name]().__repr__()}")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize flask extensions
    db.init_app(app)
    if main:
        # Initialize socketio server and attach it to the message queue, so
        # that everything works even when there are multiple servers or
        # additional processes such as Celery workers wanting to access
        # Socket.IO
        socketio.init_app(
            app, message_queue=app.config["SOCKETIO_MESSAGE_QUEUE"]
        )
    else:
        # Initialize socketio to emit events through the message queue
        # Note that since Celery does not use eventlet, we have to be explicit
        # in setting the async mode to not use it.
        socketio.init_app(
            None,
            message_queue=app.config["SOCKETIO_MESSAGE_QUEUE"],
            async_mode="threading",
        )
    celery.conf.update(config[config_name].CELERY_CONFIG)

    # Register web application routes
    from .server import main as main_blueprint

    app.register_blueprint(main_blueprint)

    # Register API routes
    from .api import api as api_blueprint

    app.register_blueprint(api_blueprint, url_prefix="/api")

    # Register async tasks support
    from .tasks import tasks_bp as tasks_blueprint

    app.register_blueprint(tasks_blueprint, url_prefix="/tasks")

    # Register events routes
    from .events import events as events_blueprint

    app.register_blueprint(events_blueprint, url_prefix="/events")

    return app


def create_server():
    return create_app(), socketio


__ALL__ = [db, celery, pdb, socketio]
