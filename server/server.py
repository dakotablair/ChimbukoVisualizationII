import os
from flask import Flask, jsonify
# render_template, json, request, jsonify

from config import config

from server.msgstats import MessageStats
from server.utils import timestamp


app = Flask(__name__)
app.config.from_object(config[os.environ.get('FLACK_CONFIG', 'development')])

# run stats per rank
stats = MessageStats()

# list to calculate request per second
request_stats = []

# Registed API routes with the application
from .api import api as api_blueprint
app.register_blueprint(api_blueprint, url_prefix='/api')


@app.before_first_request
def before_first_request():
    # for future usages
    pass


@app.before_request
def before_request():
    """Update requests per second stats."""
    t = timestamp()
    while len(request_stats) > 0 and request_stats[0] < t - 15:
        del request_stats[0]
    request_stats.append(t)


@app.route('/')
def index():
    """Serve client-side application"""
    # return render_template('index.html')
    return "Hello World"


@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify({'requests_per_second': len(request_stats) / 15})
