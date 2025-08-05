# needed for using redis in this configuration
from gevent import monkey
monkey.patch_all()

import collections
import os
import subprocess
import sys
import types

# monkey patch flask to support old version of flask_script
import flask

module_name = 'flask._compat'
my_submodule = types.ModuleType(module_name)
_compat = types.ModuleType(module_name)
_compat.text_type = str
sys.modules[module_name] = _compat
setattr(flask, '_compat', _compat)
mock_request_ctx_stack = collections.namedtuple("mock", ["top"])
mock_request_ctx_stack.top = collections.namedtuple("top", ["app"])
flask._request_ctx_stack = mock_request_ctx_stack

from flask_script import Manager, Command, Server as _Server, Option

from server import create_app, db, socketio

manager = Manager(create_app)


# Note that socketio.run(app) runs a production ready server
# when eventlet or gevent are installed. If neither of these
# are installed, then the application runs on Flask's developement
# web server, which is not appropriate for production use.
class Server(_Server):
    help = description = 'Runs the Socket.IO web server'

    def get_options(self):
        options = {
            Option('-h', '--host',
                   dest='host',
                   default=self.host),

            Option('-p', '--port',
                   dest='port',
                   type=int,
                   default=self.port),

            Option('-d', '--debug',
                   action='store_true',
                   dest='use_debugger',
                   help=('enable the Werkzeug debugger (DO NOT use in '
                         'production code'),
                   default=self.use_debugger),

            Option('-D', '--no-debug',
                   action='store_false',
                   dest='use_debugger',
                   help='disable the Werkzeug debugger',
                   default=self.use_debugger),

            Option('-r', '--reload',
                   action='store_true',
                   dest='use_reloader',
                   help=('monitor Python files for changes (not 100%% safe '
                         'for production use'),
                   default=self.use_reloader),

            Option('-R', '--no-reload',
                   action='store_false',
                   dest='use_reloader',
                   help='do not monitor Python files for changes',
                   default=self.use_reloader)
        }
        return options

    def __call__(self, app, host, port, use_debugger, use_reloader):
        # override the default runserver command to start a Socket.IO server
        if use_debugger is None:
            use_debugger = app.debug
            if use_debugger is None:
                use_debugger = True
        if use_reloader is None:
            use_reloader = app.debug
        print("host:", host, "port:", port)
        socketio.run(app,
                     host=host,
                     port=port,
                     debug=use_debugger,
                     use_reloader=use_reloader,
                     **self.server_options)

manager.add_command("runserver", Server())


class CeleryWorker(Command):
    """Starts the celery worker"""
    name = 'celery'
    capture_all_args = True

    def run(self, argv):
        ret = subprocess.call(
            ['celery', '-A', 'server.celery', 'worker'] + argv)
        sys.exit(ret)

manager.add_command("celery", CeleryWorker())


@manager.command
def createdb(drop_first=False):
    """Creates the database."""
    if drop_first:
        db.drop_all()
    db.create_all()


@manager.command
def test():
    """Runs unit tests."""
    tests = subprocess.call(['python3', '-c', 'import tests; tests.run()'])
    sys.exit(tests)


@manager.command
def lint():
    """Runs code linter"""
    lint = subprocess.call(['flake8', '--ignore=E402', 'server/', 'manage.py', 'tests/'])

    if lint:
        print('OK')
    sys.exit(lint)


if __name__ == '__main__':
    if sys.argv[1] == 'test' or sys.argv[1] == 'lint':
        os.environ['SERVER_CONFIG'] = 'testing'
        os.environ['PROVENANCE_DB'] = 'data/test/'
        os.environ['SHARDED_NUM'] = '1'
    manager.run()
