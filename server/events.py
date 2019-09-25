from flask import g, session, Blueprint, current_app, request, jsonify, abort

from . import db, socketio, celery
from .models import AnomalyStat, AnomalyData, AnomalyStatQuery, Stat, ExecData

from sqlalchemy import func, and_

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

        # query arguments
        nQueries = q.nQueries
        statKind = q.statKind

        # query column
        col = Stat.stddev
        key = 'stddev'
        if statKind == 'updates':
            col = Stat.count
            key = 'count'
        elif statKind == 'min':
            col = Stat.minimum
            key = 'minimum'
        elif statKind == 'max':
            col = Stat.maximum
            key = 'maximum'
        elif statKind == 'mean':
            col = Stat.mean
            key = 'mean'
        elif statKind == 'skewness':
            col = Stat.skewness
            key = 'skewness'
        elif statKind == 'kurtosis':
            col = Stat.kurtosis
            key = 'kurtosis'
        elif statKind == 'accumulate':
            col = Stat.accumulate
            key = 'accumulate'
        else:
            statKind = 'stddev'

        # -------------------------------------------
        # query for the latest anomaly statistics
        # -------------------------------------------
        # sub-query to get the latest anomaly statistics
        subq = db.session.query(
            AnomalyStat.app,
            AnomalyStat.rank,
            func.max(AnomalyStat.created_at).label('max_ts')
        ).group_by(AnomalyStat.app, AnomalyStat.rank).subquery('t2')

        # top 'nQueries' statistics
        stats = db.session.query(AnomalyStat).join(
            subq,
            and_(
                AnomalyStat.app == subq.c.app,
                AnomalyStat.rank == subq.c.rank,
                AnomalyStat.created_at == subq.c.max_ts
            )
        ).join(
            AnomalyStat.stat, aliased=True
        ).order_by(col.desc()).all()

        # WARNING: (race-condition), it is possible that we actually get
        # not the latest AnomalyStat. In addition, the corresponding
        # statistics are not available. Need to hadle this situation!

        top_stats = []
        bottom_stats = []
        if stats is not None and len(stats):
            nQueries = min(nQueries, len(stats))
            top_stats = [st.to_dict() for st in stats[:nQueries]]
            bottom_stats = [st.to_dict() for st in stats[-nQueries:]]

        # ---------------------------------------------------
        # processing data for the front-end
        # --------------------------------------------------
        if len(top_stats) and len(bottom_stats):
            top_dataset = {
                'name': 'TOP',
                'value': [st['stats'][key] for st in top_stats],
                'rank': [st['rank'] for st in top_stats]
            }
            bottom_dataset = {
                'name': 'BOTTOM',
                'value': [st['stats'][key] for st in bottom_stats],
                'rank': [st['rank'] for st in bottom_stats]
            }

            # broadcast the statistics to all clients
            push_data({
                'type': 'stats',
                'nQueries': nQueries,
                'statKind': statKind,
                'data': [top_dataset, bottom_dataset]
            })

        # return jsonify({}), 201


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
        'n_anomalies': 0,
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
            AnomalyStat.created_at.desc()
        ).first()

        if stat is None:
            payload.append(empty_data)
            continue

        data = stat.hist.filter(AnomalyData.step==step).first()
        if data is None:
            payload.append(empty_data)
            continue

        payload.append(data.to_dict())

    return jsonify(payload)


@celery.task
def push_execution(pid, rid, min_ts, max_ts, order, with_comm):
    from .wsgi_aux import app
    with app.app_context():
        min_ts = int(min_ts)
        execdata = ExecData.query.filter(ExecData.entry >= min_ts)
        if max_ts is not None:
            max_ts = int(max_ts)
            execdata = execdata.filter(ExecData.exit <= max_ts)

        if pid is not None:
            pid = int(pid)
            execdata = execdata.filter(ExecData.pid == pid)

        if rid is not None:
            rid = int(rid)
            execdata = execdata.filter(ExecData.rid == rid)

        if order == 'asc':
            execdata = execdata.order_by(ExecData.entry.asc())
        else:
            execdata = execdata.order_by(ExecData.entry.desc())

        execdata = [d.to_dict(int(with_comm)) for d in execdata.all()]
        if len(execdata):
            push_data({
                'type': 'execution',
                'data': execdata
            })


@events.route('/query_executions', methods=['GET'])
def get_execution():
    """
    Return a list of execution data within a given time range
    - required:
        min_ts: minimum timestamp
    - options
        max_ts: maximum timestamp
        order: [(asc) | desc]
        with_comm: 1 or (0)
        pid: program index, default None
        rid: rank index, default None
    """
    min_ts = request.args.get('min_ts', None)
    if min_ts is None:
        abort(400)

    # parse options
    max_ts = request.args.get('max_ts', None)
    order = request.args.get('order', 'asc')
    with_comm = request.args.get('with_comm', 0)
    pid = request.args.get('pid', None)
    rid = request.args.get('rid', None)

    push_execution.delay(pid, rid, min_ts, max_ts, order, with_comm)
    return jsonify({}), 200


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


