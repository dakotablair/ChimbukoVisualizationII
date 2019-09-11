from flask import g, session, Blueprint, current_app, request, jsonify

from . import db, socketio, celery
from .models import AnomalyStat, AnomalyData

import uuid

events = Blueprint('events', __name__)


def push_model(model, namespace='/events'):
    """Push the model to all connected Socket.IO clients."""
    socketio.emit('updated_model', {
        'class': model.__class__.__name__,
        'model': model.to_dict()
    }, namespace=namespace)


def push_data(data, namespace='/events'):
    """Push the data to all connected Socket.IO clients."""
    socketio.emit('updated_data', data, namespace=namespace)

@celery.task
def push_anomaly_stats():
    """Celery task that posts current anomaly statistics"""
    from .wsgi_aux import app
    with app.app_context():
        # get query condition from database
        nQueries = 7
        statKind = 'stddev'

        # query statistics from database
        top_dataset = {
            'name': 'TOP',
            'value': [100, 90, 80, 70, 60, 50, 40],
            'rank': [0, 1, 2, 3, 4, 5, 6]
        }
        bottom_dataset = {
            'name': 'BOTTOM',
            'value': [60, 50, 40, 30, 20, 10, 5],
            'rank': [10, 11, 12, 13, 14, 15, 16]
        }

        # broadcast the statistics to all clients
        push_data({
            'type': 'stats',
            'nQueries': nQueries,
            'statKind': statKind,
            'data': [top_dataset, bottom_dataset]
        })

        # clean up the database session ??
        # return jsonify({}), 200

@events.route('/stream_stats', methods=['POST'])
def stream():
    push_anomaly_stats.apply_async()
    return jsonify({}), 200

@events.route('/query_history', methods=['POST'])
def get_history():
    import random
    q = request.get_json() or {}

    ranks = q.get('qRanks', [])
    step = q.get('last_step', 0)

    payload = []
    for rank in ranks:
        rank = int(rank)
        # todo: query to database
        payload.append({
            'id': 999,
            'n_anomaly': random.randint(0, 1000),
            'step': step + 1,
            'min_timestamp': random.randint(0, 1000),
            'max_timestamp': random.randint(0, 1000)
        })

    return jsonify(payload)

# @socketio.on('status', namespace='/events')
# def events_message(message):
#     print('socketio.on.status: ', message)
#     socketio.emit('status', {'status': message['status']}, namespace='/events')

@socketio.on('query_stats', namespace='/events')
def query_stats(q):
    print(q)
    push_anomaly_stats.apply_async()

@socketio.on('connect', namespace='/events')
def events_connect():
    print('socketio.on.connect')
    # userid = str(uuid.uuid4())
    # session['userid'] = userid
    # # current_app.clients[userid] = request.namespace
    # print(userid, session['userid'])
    # socketio.emit('userid', {'userid': userid}, namespace='/events')
    # socketio.emit('status', {'status': 'Connected user', 'userid': userid}, namespace='/events')

@socketio.on('disconnect', namespace='/events')
def events_disconnect():
    print('socketio.on.disconnect')
    # del current_app.clients[session['userid']]
    # print('Client %s disconnected' % session['userid'])


