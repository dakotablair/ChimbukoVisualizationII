# needed (?) for using redis in this configuration
from gevent import monkey
monkey.patch_all()

import click  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import os  # noqa: E402

from server import create_server  # noqa: E402


@click.group()
def cli():
    pass


@cli.command()
@click.option('--host', default='0.0.0.0', help='The interface to bind to.')
@click.option('--port', default=5000, help='The listening port.', type=int)
def runserver(host, port):
    """Runs the Flask app."""
    app, sio = create_server()
    sio.run(app, host=host, port=port)


@click.command()
def createdb(drop_first=False):
    pass


@cli.command
def test():
    """Runs unit tests."""
    tests = subprocess.call(["python3", "-c", "import tests; tests.run()"])
    sys.exit(tests)


@cli.command
def lint():
    """Runs code linter"""
    lint = subprocess.call(
        ["flake8", "--ignore=E402", "server/", "manager.py", "tests/"]
    )
    sys.exit(lint)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("lint", "test"):
        os.environ["SERVER_CONFIG"] = "testing"
        os.environ["PROVENANCE_DB"] = "data/test/"
        os.environ["SHARDED_NUM"] = "1"
    cli()
