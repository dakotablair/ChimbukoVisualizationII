import subprocess
import sys
from flask_script import Manager

from server import create_app

manager = Manager(create_app)

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
    manager.run()