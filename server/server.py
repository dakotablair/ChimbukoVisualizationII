import os
from flask import Flask, request, jsonify
# render_template, json

from config import config

from server.msgstats import MessageStats


app = Flask(__name__)
app.config.from_object(config[os.environ.get('FLACK_CONFIG', 'development')])

# run stats per rank
stats = MessageStats()


@app.route('/api/messages', methods=['POST'])
def new_message():
    """Post a new message"""
    if request.headers['Content-Type'] == 'application/json':
        msg = request.get_json()

        # process message (running statistics)
        rank = int(msg['rank'])
        stats.update(rank, msg['data'])
        # end of process

        return "OK"
    else:
        return "415 Unsupported Media Type"


@app.route('/api/stat/<int:rank>', methods=['GET'])
def get_stat(rank):
    """Return running statistics (mean and std. dev.)"""
    mean, std = stats.get(int(rank))
    return jsonify({'mean': mean, 'stddev': std})


@app.route('/')
def index():
    """Serve client-side application"""
    # return render_template('index.html')
    return "Hello World"
