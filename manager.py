import subprocess
import sys
import os
from flask_script import Manager, Command

from server import create_app, db

manager = Manager(create_app)


class CeleryWorker(Command):
    """Starts the celery worker"""
    name = 'celery'
    capture_all_args = True

    def run(self, argv):
        ret = subprocess.call(
            ['celery', 'worker', '-A', 'server.celery'] + argv)
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
    tests = subprocess.call(['python', '-c', 'import tests; tests.run()'])
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
    manager.run()
