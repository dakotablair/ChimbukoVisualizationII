from flask import request, jsonify, abort

from .. import db
from ..models import AnomalyStat, AnomalyData, FuncStat, Stat
from . import api
from ..tasks import make_async
from ..utils import timestamp, url_for
from requests import post

from sqlalchemy.exc import IntegrityError
from runstats import Statistics
from sqlalchemy import func, and_


def process_on_anomaly(data:list, ts):
    """
    process on anomaly data before adding to database
    """
    anomaly_stat = []
    anomaly_data = []
    stat = []

    for d in data:
        if 'key' in d:
            app, rank = d['key'].split(':')
            app = int(app)
            rank = int(rank)
        else:
            app = d.get('app')
            rank = d.get('rank')
        key = '{}:{}'.format(app, rank)
        key_ts = '{}:{}'.format(key, ts)
        anomaly_stat.append({
            'key': key,
            'key_ts': key_ts,
            'app': app,
            'rank': rank,
            'created_at': ts
        })

        d['stats'].update({'kind': 'anomaly', 'anomalystat_key': key_ts})
        stat.append(d['stats'])

        if 'data' in d:
            [dd.update({
                'anomalystat_key': key,
                'funcstat_key': None,
            }) for dd in d['data']]
            anomaly_data += d['data']

    return anomaly_stat, anomaly_data, stat


def process_on_func(data:list, ts):
    func_stat = []
    stat = []

    for d in data:
        key_ts = '{}:{}'.format(d['fid'], ts)
        func_stat.append({
            'created_at': ts,
            'key_ts': key_ts,
            'fid': d['fid'],
            'name': d['name']
        })
        d['stats'].update({
            'kind': 'stats',
            'funcstat_key': key_ts,
            'anomalystat_key': None
        })
        stat.append(d['stats'])
        d['inclusive'].update({
            'kind': 'inclusive',
            'funcstat_key': key_ts,
            'anomalystat_key': None
        })
        stat.append(d['inclusive'])
        d['exclusive'].update({
            'kind': 'exclusive',
            'funcstat_key': key_ts,
            'anomalystat_key': None
        })
        stat.append(d['exclusive'])

    return func_stat, stat


def delete_old_anomaly():
    subq = db.session.query(
        AnomalyStat.app,
        AnomalyStat.rank,
        func.max(AnomalyStat.created_at).label('max_ts')
    ).group_by(AnomalyStat.app, AnomalyStat.rank).subquery('t2')

    ret = [ [d.id, d.key_ts] for d in db.session.query(AnomalyStat).join(
        subq,
        and_(
            AnomalyStat.app == subq.c.app,
            AnomalyStat.rank == subq.c.rank,
            AnomalyStat.created_at < subq.c.max_ts
        )
    ).all()]

    ids = [q[0] for q in ret]
    keys = [q[1] for q in ret]

    db.engine.execute(
        AnomalyStat.__table__.delete().where(AnomalyStat.id.in_(ids))
    )
    db.engine.execute(
        Stat.__table__.delete().where(Stat.anomalystat_key.in_(keys))
    )


def delete_old_func():
    subq = db.session.query(
        FuncStat.fid,
        func.max(FuncStat.created_at).label('max_ts')
    ).group_by(FuncStat.fid).subquery('t2')

    ret = [[d.id, d.key_ts] for d in db.session.query(FuncStat).join(
        subq,
        and_(
            FuncStat.fid == subq.c.fid,
            FuncStat.created_at < subq.c.max_ts
        )
    ).all()]

    ids = [q[0] for q in ret]
    keys = list(set([q[1] for q in ret]))

    db.engine.execute(
        FuncStat.__table__.delete().where(FuncStat.id.in_(ids))
    )
    db.engine.execute(
        Stat.__table__.delete().where(Stat.funcstat_key.in_(keys))
    )


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
                    "accumulate": (float),
                    "minimum": (float),
                    "maximum": (float),
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

    ts = data.get('created_at', None)
    if ts is None:
        abort(400)

    try:
        anomaly_head, anomaly_data, anomaly_stat = \
            process_on_anomaly(data.get('anomaly', []), ts)
        func_head, func_stat = process_on_func(data.get('func', []), ts)

        if len(anomaly_head):
            db.engine.execute(AnomalyStat.__table__.insert(), anomaly_head)

        if len(anomaly_data):
            db.engine.execute(AnomalyData.__table__.insert(), anomaly_data)

        if len(anomaly_stat):
            db.engine.execute(Stat.__table__.insert(), anomaly_stat)

        if len(func_head):
            db.engine.execute(FuncStat.__table__.insert(), func_head)

        if len(func_stat):
            db.engine.execute(Stat.__table__.insert(), func_stat)

        # although we have defined models to enable cascased delete operation,
        # it actually didn't work. The reason is that we do the bulk insertion
        # to get performance and, for now, I couldn't figure out how to define
        # backreference in the above bulk insertion. So that, we do delete
        # Stat rows manually (but using bulk deletion)
        delete_old_anomaly()
        delete_old_func()
    except Exception as e:
        print(e)

    # notify
    # post(url_for('events.stream', _external=True))

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
    app = request.args.get('app', default=None)
    rank = request.args.get('rank', default=None)

    subq = db.session.query(
        AnomalyStat.app,
        AnomalyStat.rank,
        func.max(AnomalyStat.created_at).label('max_ts')
    ).group_by(AnomalyStat.app, AnomalyStat.rank).subquery('t2')

    q = db.session.query(AnomalyStat).join(
        subq,
        and_(
            AnomalyStat.app == subq.c.app,
            AnomalyStat.rank == subq.c.rank,
            AnomalyStat.created_at == subq.c.max_ts
        )
    )

    if app is not None and rank is not None:
        stats = q.filter(AnomalyStat.app==int(app), AnomalyStat.rank==int(rank)).all()
    else:
        stats = q.all()

    return jsonify([st.to_dict() for st in stats])


@api.route('/anomalydata', methods=['GET'])
def get_anomalydata():
    app = request.args.get('app', default=None)
    rank = request.args.get('rank', default=None)
    limit = request.args.get('limit', default=None)

    stat = AnomalyStat.query.filter(
        and_(
            AnomalyStat.app==int(app),
            AnomalyStat.rank==int(rank)
        )
    ).order_by(
        AnomalyStat.created_at.desc()
    ).first()

    if limit is None:
        data = stat.hist.order_by(AnomalyData.step.desc()).all()
    else:
        data = stat.hist.order_by(AnomalyData.step.desc()).limit(limit).all()
    data.reverse()

    return jsonify([dd.to_dict() for dd in data])


@api.route('/funcstats', methods=['GET'])
def get_funcstats():
    fid = request.args.get('fid', default=None)

    subq = db.session.query(
        FuncStat.fid,
        func.max(FuncStat.created_at).label('max_ts')
    ).group_by(FuncStat.fid).subquery('t2')

    q = db.session.query(FuncStat).join(
        subq,
        and_(
            FuncStat.fid == subq.c.fid,
            FuncStat.created_at == subq.c.max_ts
        )
    )

    if fid is None:
        stats = q.all()
    else:
        stats = q.filter(FuncStat.fid == int(fid)).all()

    return jsonify([st.to_dict() for st in stats])
