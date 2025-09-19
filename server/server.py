import json
import os

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    render_template,
)

from . import stats as req_stats
from . import socketio, celery as mycelery
from . import pdb

main = Blueprint('main', __name__)


@main.route('/build')
def build():
    with open("./frontend/v1/package.json") as f:
        npm_package = json.load(f)
    return jsonify({
        "npm_package_version": npm_package["version"]
    })


@main.before_app_request
def before_request():
    """Update requests per second stats."""
    req_stats.add_request()


@main.route('/stop')
def stop():
    import time

    global pdb

    def get_inspect():
        from requests import get
        resp = get(current_app.url_for('tasks.get_info', _external=True))
        info = resp.json()
        return info

    max_tries = 1000
    n_try = 0
    n_tasks = 0
    while n_try < max_tries:
        inspect = get_inspect()

        n_tasks = 0

        # no running celery workers
        if inspect.get('stats') is None:
            break

        active = inspect.get('active')
        if active is not None and isinstance(active, dict):
            n_tasks += sum([len(v) for _, v in active.items()])

        scheduled = inspect.get('scheduled')
        if scheduled is not None and isinstance(scheduled, dict):
            n_tasks += sum([len(v) for _, v in scheduled.items()])

        if n_tasks == 0:
            break

        print('remained celery tasks: ', n_tasks)
        n_try += 1
        time.sleep(10)

    print('Before shutdown celery workers...')
    print('remained celery tasks: ', n_tasks)

    mycelery.control.broadcast('shutdown')
    socketio.stop()
    print("Shutting down SocketIO web server!")

    if 'pdb' in globals():
        del pdb
    print("Shutting down provdb!")
    return jsonify({})


@main.route('/')
def index():
    """Serve client-side application"""
    # return render_template('index_v0.html')
    return render_template('index.html')


@main.route('/stats', methods=['GET'])
def get_stats():
    return jsonify({'requests_per_second': req_stats.requests_per_second()})
