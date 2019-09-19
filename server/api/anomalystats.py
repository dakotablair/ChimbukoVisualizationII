from flask import request, jsonify

from .. import db
from ..models import AnomalyStat, AnomalyData
from . import api
from ..tasks import make_async
from ..utils import timestamp, url_for
from requests import post

from sqlalchemy.exc import IntegrityError
from runstats import Statistics
from sqlalchemy import func, and_


def get_or_create_stats(app_rank: str):
    """
    Get or create AnomalyStat object

    Ref: http://rachbelaid.com/handling-race-condition-insert-with-sqlalchemy/
    """
    app, rank = app_rank.split(':')
    app = int(app)
    rank = int(rank)

    # looking for an existing AnomalyStat object for given app and rank
    stat = AnomalyStat.query.filter_by(app=app, rank=rank).first()

    # An AnomalyStat object exist, then return it
    if stat is not None:
        return stat

    # An AnomalyStat object doesn't exist so we create an instance
    stat = AnomalyStat.create({'app': app, 'rank': rank})

    # we create a savepoint in case of race condition
    db.session.begin_nested()
    try:
        # we try to insert and release the savepoint
        db.session.add(stat)
        db.session.commit()
    except IntegrityError:
        # The insert fail due to a concurrent transaction
        db.session.rollback()
        # we get the AnomalyStat object which exist now
        stat = get_or_create_stats(app_rank)

    return stat


def create_or_update_stats(app, rank, stats: Statistics):
    """
    Create or update AnomalyStat object
    """

    # looking for an existing AnomalyStat object for given app and rank
    curr_stats = AnomalyStat.query.filter_by(app=app, rank=rank).\
        order_by(AnomalyStat.count.desc()).first()

    # An AnomalyStat object doesn't exist, then create new one
    if curr_stats is None:
        curr_stats = AnomalyStat.create_from(app, rank, stats)
        db.session.begin_nested()
        try:
            db.session.add(curr_stats)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            curr_stats = create_or_update_stats(app, rank, stats)
        return curr_stats

    curr_id = curr_stats.id
    st = curr_stats.to_stats()
    st += stats

    new_id = '{}:{}:{}'.format(app, rank, int(curr_id.split(':')[-1]) + 1)
    new_stats = AnomalyStat.create_from(app, rank, st, new_id)

    db.session.begin_nested()
    try:
        # To avoid race-condition, we actually don't update
        # the existing row but new row is added. Then, 'deleted'
        # field of the previous row is set to false.
        # We need to take care on this later.
        db.session.add(new_stats)
        curr_stats.deleted = True
        db.session.commit()
    except IntegrityError:
        # The update fails due to a concurrent transaction
        db.session.rollback()
        curr_stats = create_or_update_stats(app, rank, stats)

    return curr_stats


@api.route('/anomalydata', methods=['POST'])
@make_async
def new_anomalydata():
    """
    Register anomaly data

    - structure
    {
        "created_at": (integer),
        "anomaly": [
            {
                "key": "{app}:{rank}",   // app == pid, todo: append timestamp?
                "stats": {               // statistics
                    // todo: "anomalystat_key": "{app}:{rank}:{ts}"
                    "count": (integer),
                    "acc": (float),
                    "min": (float),
                    "max": (float),
                    "mean": (float),
                    "stddev": (float),
                    "skewness": (float),
                    "kurtosis": (float)
                },
                "data": [         // AnomalyData
                    {
                        "app": (integer),
                        "rank": (integer),
                        "step": (integer),
                        "min_timestamp": (integer),
                        "max_timestamp": (integer),
                        "n_anomalies": (integer),
                        "stat_id": (integer)  // must matched with "key"
                    }
                ]
            }
        ],
        "func": [
            {
                // todo: "funcstat_key": "{fid}:{ts}"
                "fid": (integer),
                "name": (string),
                "stats": { statistics },
                "inclusive": { statistics },
                "exclusive": { statistics }
            }
        ]
    }

    """
    data = request.get_json() or {}
    if isinstance(data, list):
        payload = data
        delete_old = True
    else:
        payload = data.get('payload', None)
        delete_old = data.get('delete_old', True)

    if not isinstance(payload, list):
        payload = [payload]

    _stats = []
    _data = []

    ts = timestamp()
    for anomalydata in payload:
        if anomalydata is None:
            continue

        _stat = {}
        # Basic information
        if 'key' in anomalydata:
            key = anomalydata['key']
            app, rank = key.split(':')
            anomalydata['app'] = int(app)
            anomalydata['rank'] = int(rank)

        _stat['app'] = int(anomalydata['app'])
        _stat['rank'] = int(anomalydata['rank'])
        _stat['created_at'] = int(anomalydata['created_at']) \
            if 'created_at' in anomalydata else ts

        # Statistics
        _s = anomalydata['stats']
        _stat['n_updates'] = int(_s['n_updates'])
        _stat['n_anomalies'] = int(_s['n_anomalies'])
        _stat['n_min_anomalies'] = int(_s['n_min_anomalies'])
        _stat['n_max_anomalies'] = int(_s['n_max_anomalies'])
        _stat['mean'] = float(_s['mean'])
        _stat['stddev'] = float(_s['stddev'])
        _stat['skewness'] = float(_s['skewness']
                                 if 'skewness' in anomalydata['stats'] else 0)
        _stat['kurtosis'] = float(_s['kurtosis']
                                 if 'kurtosis' in anomalydata['stats'] else 0)

        # key for reference
        key = '{}:{}'.format(_stat['app'], _stat['rank'])
        _stat['key'] = anomalydata['key'] if 'key' in anomalydata else key
        _stats.append(_stat)

        # data
        for _d in anomalydata['data']:
            if 'stat_id' not in _d:
                _d['stat_id'] = key
        _data.extend(anomalydata['data'])

    # insert stats to AnomalyStat Table
    if len(_stats):
        db.engine.execute(AnomalyStat.__table__.insert(), _stats)

    # insert data to AnomalyData Table
    if len(_data):
        db.engine.execute(AnomalyData.__table__.insert(), _data)

    # delete old AnomalyStat rows
    if delete_old:
        subq = db.session.query(
            AnomalyStat.app,
            AnomalyStat.rank,
            func.max(AnomalyStat.n_updates).label('max_n_updates')
        ).group_by(
            AnomalyStat.app, AnomalyStat.rank
        ).subquery('t2')

        ids = [d.id for d in db.session.query(AnomalyStat).join(
            subq,
            and_(
                AnomalyStat.app == subq.c.app,
                AnomalyStat.rank == subq.c.rank,
                AnomalyStat.n_updates < subq.c.max_n_updates
            )
        ).all()]

        db.engine.execute(
            AnomalyStat.__table__.delete().where(
                AnomalyStat.id.in_(ids)
            )
        )

    # notify
    post(url_for('events.stream', _external=True))

    # todo: make information output with Location
    return jsonify({}), 201

@api.route('/anomalystats', methods=['GET'])
def get_anomalystats():
    """
    Return anomaly stat specified by app and rank index
    - (e.g.) /api/anomalystats will return all available statistics
    - (e.g.) /api/anomalystats?app=0&rank=0 will return statistics of
                 application index is 0 and rank index is 0.
    - return 400 error if there are no available statistics
    """
    subq = db.session.query(
        AnomalyStat.app,
        AnomalyStat.rank,
        func.max(AnomalyStat.n_updates).label('max_n_updates')
    ).group_by(AnomalyStat.app, AnomalyStat.rank).subquery('t2')

    stats = db.session.query(AnomalyStat).join(
        subq,
        and_(
            AnomalyStat.app == subq.c.app,
            AnomalyStat.rank == subq.c.rank,
            AnomalyStat.n_updates == subq.c.max_n_updates
        )
    ).all()

    return jsonify([st.to_dict() for st in stats])


@api.route('/anomalydata', methods=['GET'])
def get_anomalydata():
    app = request.args.get('app', default=None)
    rank = request.args.get('rank', default=None)

    stat = AnomalyStat.query.filter(
        and_(
            AnomalyStat.app==int(app),
            AnomalyStat.rank==int(rank)
        )
    ).order_by(
        AnomalyStat.n_updates.desc()
    ).first()

    data = stat.data.all()

    return jsonify({
        'stat': stat.to_dict(),
        'data': [d.to_dict() for d in data]
    })
