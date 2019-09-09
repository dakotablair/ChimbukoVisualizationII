import os

from . import create_app

# Create an application instance that auxiliary processes such as Celery
# workers can use
application = app = create_app(os.environ.get('SERVER_CONFIG', 'production'), main=False)
