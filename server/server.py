import os
from flask import Flask, request, jsonify
# render_template, json

from config import config

from runstats import Statistics
from collections import defaultdict
import threading

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config.from_object(config[os.environ.get('FLACK_CONFIG', 'development')])

# run stats per rank
stats = defaultdict(lambda: Statistics())
lock = threading.Lock()


def update_stats(rank, data):
    with lock:
        for num in data:
            stats[rank].push(num)


def print_stats(rank):
    with lock:
        print("Rank {} - mean: {}, std: {}".format(
            rank, stats[rank].mean(), stats[rank].stddev()))


def get_stats(rank):
    with lock:
        return stats[rank].mean(), stats[rank].stddev()
# end of run stats


@app.route('/api/messages', methods=['POST'])
def new_message():
    """Post a new message"""
    if request.headers['Content-Type'] == 'application/json':
        msg = request.get_json()

        # process message (running statistics)
        rank = int(msg['rank'])
        update_stats(rank, msg['data'])
        # print_stats(rank)
        # end of process

        return "OK"
    else:
        return "415 Unsupported Media Type"


@app.route('/api/stat/<int:rank>', methods=['GET'])
def get_stat(rank):
    """Return running statistics (mean and std. dev.)"""
    mean, std = get_stats(int(rank))
    return jsonify({'mean': mean, 'stddev': std})


@app.route('/')
def index():
    """Serve client-side application"""
    # return render_template('index.html')
    return "Hello World"
