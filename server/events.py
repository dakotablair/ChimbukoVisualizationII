from flask import g, session, Blueprint, current_app, request, jsonify

from . import db, socketio, celery
from .models import AnomalyStat, AnomalyData, AnomalyStatQuery

from sqlalchemy import func, and_
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
        q = AnomalyStatQuery.query.\
            order_by(AnomalyStatQuery.created_at.desc()).first()
        if q is None:
            q = AnomalyStatQuery.create({'nQueries': 5, 'statKind': 'stddev'})
            db.session.add(q)
            db.session.commit()

        nQueries = q.nQueries
        statKind = q.statKind

        col = AnomalyStat.stddev
        key = 'stddev'
        if statKind == 'updates':
            col = AnomalyStat.n_updates
            key = 'n_updates'
        elif statKind == 'min':
            col = AnomalyStat.n_min_anomalies
            key = 'n_min_anomalies'
        elif statKind == 'max':
            col = AnomalyStat.n_max_anomalies
            key = 'n_max_anomalies'
        elif statKind == 'mean':
            col = AnomalyStat.mean
            key = 'mean'
        elif statKind == 'skewness':
            col = AnomalyStat.skewness
            key = 'skewness'
        elif statKind == 'kurtosis':
            col = AnomalyStat.kurtosis
            key = 'kurtosis'
        else:
            statKind = 'stddev'

        # query statistics from database
        subq = db.session.query(
            AnomalyStat.app,
            AnomalyStat.rank,
            func.max(AnomalyStat.n_updates).label('max_n_updates')
        ).group_by(AnomalyStat.app, AnomalyStat.rank).subquery('t2')

        top_stats = db.session.query(AnomalyStat).join(
            subq,
            and_(
                AnomalyStat.app == subq.c.app,
                AnomalyStat.rank == subq.c.rank,
                AnomalyStat.n_updates == subq.c.max_n_updates
            )
        ).order_by(col.desc()).limit(nQueries).all()
        top_stats = [st.to_dict() for st in top_stats]

        bottom_stats = AnomalyStat.query.join(
            subq,
            and_(
                AnomalyStat.app == subq.c.app,
                AnomalyStat.rank == subq.c.rank,
                AnomalyStat.n_updates == subq.c.max_n_updates
            )
        ).order_by(col.asc()).limit(nQueries).all()
        bottom_stats = [st.to_dict() for st in bottom_stats]

        if len(top_stats) and len(bottom_stats):
            top_dataset = {
                'name': 'TOP',
                'value': [st[key] for st in top_stats],
                'rank': [st['rank'] for st in top_stats]
            }
            bottom_dataset = {
                'name': 'BOTTOM',
                'value': [st[key] for st in bottom_stats],
                'rank': [st['rank'] for st in bottom_stats]
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
    q = request.get_json() or {}

    app = 0
    ranks = q.get('qRanks', [])
    step = q.get('last_step', 0)
    if step is None:
        step = -1

    empty_data = {
        'id': -1,
        'n_anomaly': 0,
        'step': step,
        'min_timestamp': 0,
        'max_timestamp': 0
    }
    step += 1

    payload = []
    for rank in ranks:
        rank = int(rank)

        stat = AnomalyStat.query.filter(
            and_(
                AnomalyStat.app == app,
                AnomalyStat.rank == rank
            )
        ).order_by(
            AnomalyStat.n_updates.desc()
        ).first()

        if stat is None:
            payload.append(empty_data)
            continue

        data = stat.data.filter(AnomalyData.step==step).first()
        if data is None:
            payload.append(empty_data)
            continue

        payload.append(data.to_dict())

    return jsonify(payload)


@socketio.on('query_stats', namespace='/events')
def query_stats(q):
    nQueries = q.get('nQueries', 5)
    statKind = q.get('statKind', 'stddev')

    q = AnomalyStatQuery.create({'nQueries': nQueries, 'statKind': statKind})
    db.session.add(q)
    db.session.commit()

    push_anomaly_stats.apply_async()


@events.route('/query_stats', methods=['POST'])
def post_query_stats():
    q = request.get_json()

    nQueries = q.get('nQueries', 5)
    statKind = q.get('statKind', 'stddev')

    q = AnomalyStatQuery.create({'nQueries': nQueries, 'statKind': statKind})
    db.session.add(q)
    db.session.commit()

    return jsonify({"ok": True})


@socketio.on('connect', namespace='/events')
def events_connect():
    print('socketio.on.connect')


@socketio.on('disconnect', namespace='/events')
def events_disconnect():
    print('socketio.on.disconnect')


