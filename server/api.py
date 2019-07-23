from flask import Blueprint, request, jsonify
# g, abort

from .server import stats

api = Blueprint('api', __name__)


@api.route('/messages', methods=['POST'])
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


@api.route('/stat/<int:rank>', methods=['GET'])
def get_stat(rank):
    """Return running statistics (mean and std. dev.)"""
    mean, std, count = stats.get(int(rank))
    return jsonify({'mean': mean, 'stddev': std, 'count': count})
