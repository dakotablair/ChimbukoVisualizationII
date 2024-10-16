# needed (?) for using redis in this configuration
# from gevent import monkey
# monkey.patch_all()

import click  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import os  # noqa: E402

from flask_socketio import SocketIO, emit, send

from server import create_app  # , socketio  # noqa: E402


@click.group()
def cli():
    pass


@cli.command()
@click.option('--host', default='0.0.0.0', help='The interface to bind to.')
@click.option('--port', default='5000', help='The listening port.')
def runserver(host, port):
    """Runs the Flask app."""
    app = create_app()
    socketio = SocketIO(app, engineio_logger=True)

    @socketio.on("connect")
    def connect():
        print("client connected")

    @socketio.on("disconnect")
    def disconnect():
        print("client disconnected")

    @socketio.on("message")
    def echo(data):
        print(f"received message: {data}")
        emit("received data", brodcast=True)

    @socketio.on("ping")
    def ping(data=None):
        send(f"pong! ;) {data=}")

    socketio.run(app, host=host, port=port)


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
    # print(f"MONKEY PATCHED {eventlet.patcher.is_monkey_patched(click)}")
    if len(sys.argv) > 1 and sys.argv[1] in ("lint", "test"):
        os.environ["SERVER_CONFIG"] = "testing"
        os.environ["PROVENANCE_DB"] = "data/test/"
        os.environ["SHARDED_NUM"] = "1"
    cli()
    print(__name__)
