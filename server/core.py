import os

from celery import Celery
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

# from .provdb import ProvDB
from .mock import MockPDB


pdb = MockPDB()

db = SQLAlchemy()
socketio = SocketIO(async_mode='gevent', engineio_logger=True)
"""
pdb = ProvDB(
    pdb_path=os.environ.get("PROVENANCE_DB", ""),
    pdb_sharded_num=int(os.environ.get("SHARDED_NUM", 0)),
    pdb_addr=os.environ.get("PROVDB_ADDR", ""),
    pdb_ninstance=int(os.environ.get("PROVDB_NINSTANCE", 1)),
    pdb_addr_path=os.environ.get("PROVDB_ADDR_PATH", ""),
)
"""
celery = Celery(
    __name__,
    broker=os.environ.get("CELERY_BROKER_URL", "redis://"),
    backend=os.environ.get("CELERY_BROKER_URL", "redis://"),
)
celery.config_from_object("celeryconfig")


# Import models so that they are registered with SQLAlchemy
from . import models  # noqa

# Import celery task so that it is registered with the Celery workers
from .tasks import run_flask_request  # noqa
