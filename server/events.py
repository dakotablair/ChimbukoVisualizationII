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
        n = 5
        orderby = 'stddev'

        # query statistics from database
        x = []
        y = []
        z = []

        # broadcast the statistics to all clients
        push_data({
            # 'type': 'anomaly_stats',
            # 'n': n,
            # 'orderby': orderby,
            'top': {
                'x': [0, 1, 2, 3, 4],
                'y': [100, 90, 80, 70, 60],
                'z': ['Rank0', 'Rank1', 'Rank2', 'Rank3', 'Rank4']
            },
            'bottom': {
                'x': [0, 1, 2, 3, 4],
                'y': [50, 40, 30, 20, 10],
                'z': ['Rank99', 'Rank98', 'Rank97', 'Rank96', 'Rank95']
            }
        })

        # clean up the database session ??
        # return jsonify({}), 200

@events.route('/stream_stats', methods=['POST'])
def stream():
    print('/stream_stats')

    # query to db
    push_anomaly_stats.apply_async()

    return jsonify({}), 200

@socketio.on('status', namespace='/events')
def events_message(message):
    print('socketio.on.status: ', message)
    socketio.emit('status', {'status': message['status']}, namespace='/events')

@socketio.on('connect', namespace='/events')
def events_connect():
    print('socketio.on.connect')
    userid = str(uuid.uuid4())
    session['userid'] = userid
    # current_app.clients[userid] = request.namespace
    print(userid, session['userid'])
    socketio.emit('userid', {'userid': userid}, namespace='/events')
    socketio.emit('status', {'status': 'Connected user', 'userid': userid}, namespace='/events')

@socketio.on('disconnect', namespace='/events')
def events_disconnect():
    print('socketio.on.disconnect')
    # del current_app.clients[session['userid']]
    print('Client %s disconnected' % session['userid'])


