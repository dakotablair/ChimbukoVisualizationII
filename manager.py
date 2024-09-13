
# import eventlet

# eventlet.monkey_patch()

import click
# click = eventlet.import_patched("click")
import subprocess  # noqa: E402
import sys  # noqa: E402
import os  # noqa: E402, F401

from server import create_app  # noqa: E402

# def create_app():
#     pass


# manager = Manager(create_app)
class M:
    def add_command(*args):
        print(args)


manager = M()


@click.group()
def cli():
    pass


@click.command()
def runserver():
    """Runs the Flask app."""
    app = create_app()
    app.run()


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
