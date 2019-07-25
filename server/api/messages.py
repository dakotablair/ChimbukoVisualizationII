from flask import request, jsonify

from .. import msg_stats
from . import api


@api.route('/messages', methods=['POST'])
def new_message():
    """Post a new message"""
    if request.headers['Content-Type'] == 'application/json':
        msg = request.get_json()

        # process message (running statistics)
        rank = int(msg['rank'])
        msg_stats.update(rank, msg['data'])
        # end of process


        return "OK"
    else:
        return "415 Unsupported Media Type"


@api.route('/stat/<int:rank>', methods=['GET'])
def get_stat(rank):
    """Return running statistics (mean and std. dev.)"""
    mean, std, count = msg_stats.get(int(rank))
    return jsonify({'mean': mean, 'stddev': std, 'count': count})
