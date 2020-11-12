import os
from flask import request, jsonify, abort, current_app

from .. import db
from ..models import AnomalyStat, AnomalyData, FuncStat, AnomalyStatQuery
from . import api
from ..tasks import make_async
from ..utils import timestamp, url_for
from requests import post
from ..events import push_data

from sqlalchemy.exc import IntegrityError
from runstats import Statistics
from sqlalchemy import func, and_

import json


def process_on_anomaly(data: list, ts):
    """
    process on anomaly data before adding to database
    """
    anomaly_stat = []
    anomaly_data = []

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

        stat = d['stats']
        stat.update({
            'key': key,
            'key_ts': key_ts,
            'app': app,
            'rank': rank,
            'created_at': ts
        })
        anomaly_stat.append(stat)

        if 'data' in d:
            anomaly_data += d['data']

    return anomaly_stat, anomaly_data


def process_on_func(data: list, ts):
    def getStat(stat: dict, prefix):
        d = {}
        for k, v in stat.items():
            d["{}_{}".format(prefix, k)] = v
        return d

    func_stat = []
    for d in data:
        key_ts = '{}:{}'.format(d['fid'], ts)
        base = {
            'created_at': ts,
            'key_ts': key_ts,
            'fid': d['fid'],
            'name': d['name']
        }

        base.update(getStat(d['stats'], 'a'))
        base.update(getStat(d['inclusive'], 'i'))
        base.update(getStat(d['exclusive'], 'e'))

        func_stat.append(base)

    return func_stat


def delete_all_db():
    try:
        num_rows_deleted = db.session.query(AnomalyStat).delete()
        db.session.commit()
        num_rows_deleted = db.session.query(AnomalyData).delete()
        db.session.commit()
        num_rows_deleted = db.session.query(FuncStat).delete()
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()


def delete_old_anomaly():
    subq = db.session.query(
        AnomalyStat.app,
        AnomalyStat.rank,
        func.max(AnomalyStat.created_at).label('max_ts')
    ).group_by(AnomalyStat.app, AnomalyStat.rank).subquery('t2')

    ret = [[d.id, d.key_ts] for d in db.session.query(AnomalyStat).join(
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
    # db.engine.execute(
    #     Stat.__table__.delete().where(Stat.anomalystat_key.in_(keys))
    # )


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
    # db.engine.execute(
    #     Stat.__table__.delete().where(Stat.funcstat_key.in_(keys))
    # )


def push_anomaly_stat(q, anomaly_stats: list, anomaly_counters):

    # query arguments
    nQueries = q.nQueries
    statKind = q.statKind

    anomaly_stats.sort(key=lambda d: d[statKind], reverse=True)

    top_stats = []
    # bottom_stats = []
    if anomaly_stats is not None and len(anomaly_stats):
        nQueries = min(nQueries, len(anomaly_stats))
        top_stats = anomaly_stats[:nQueries]
        # bottom_stats = anomaly_stats[-nQueries:][::-1]

    # ---------------------------------------------------
    # processing data for the front-end
    # --------------------------------------------------
    if len(top_stats):  # and len(bottom_stats):
        top_dataset = {
            'name': 'Top Ranks',
            'stat': top_stats,
        }
        bottom_dataset = {
            'name': 'CPU/GPU Counters',
            'stat': anomaly_counters,
        }
        # broadcast the statistics to all clients
        push_data({
            'nQueries': nQueries,
            'statKind': statKind,
            'data': [top_dataset, bottom_dataset]
        }, 'update_stats')


def push_anomaly_data(q, anomaly_data: list):
    q = q.to_dict()
    ranks = q.get('ranks', [])

    if len(ranks) == 0:
        return

    selected = list(filter(lambda d: d['rank'] in ranks, anomaly_data))
    selected.sort(key=lambda d: d['min_timestamp'])
    push_data(selected, 'update_history')


@api.route('/anomalydata', methods=['POST'])
@make_async
def new_anomalydata():
    """
    Register anomaly data

    - structure
    {
        'anomaly_stats': (dict), (optional) // anomaly stats, see details below
        'counter_stats': [
            {
                'app': (string) // program index,
                'counter': (string) // counter description,
                'stats': { // global aggregated statistics
                    "count": (integer),
                    "accumulate": (float),
                    "minimum": (float),
                    "maximum": (float),
                    "mean": (float),
                    "stddev": (float),
                    "skewness": (float),
                    "kurtosis": (float)
                }
            }
        ]
    }
    - structure for 'anomaly_stats'
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
    # print('new_anomalydata')
    data = request.get_json() or {}

    # for the case empty anomaly data were sent
    if 'anomaly_stats' not in data:
        return jsonify({}), 201

    anomaly_stats = data['anomaly_stats']
    counter_stats = data.get('counter_stats', [])

    ts = anomaly_stats.get('created_at', None)
    if ts is None:
        abort(400)

    # process counter stats
    anomaly_counters = []
    cpu_counters = ['cpu: User %',
                    'cpu: Idle %',
                    'cpu: System %']
    gpu_counters = ['GPU Occupancy (Warps)',
                    'Local Memory (bytes per thread)',
                    'Shared Static Memory (bytes)']
    if counter_stats:
        for d in counter_stats:
            if d['counter'] in gpu_counters or \
               d['counter'] in cpu_counters:
                anomaly_counters.append(d)

    # print('processing...')
    anomaly_stat, anomaly_data = \
        process_on_anomaly(anomaly_stats.get('anomaly', []), ts)
    func_stat = process_on_func(anomaly_stats.get('func', []), ts)

    # print('update db...')
    try:
        if len(anomaly_stat):
            db.get_engine(app=current_app, bind='anomaly_stats').execute(
                AnomalyStat.__table__.insert(), anomaly_stat
            )
            db.get_engine(app=current_app, bind='anomaly_data').execute(
                AnomalyData.__table__.insert(), anomaly_data
            )
        if len(func_stat):
            db.get_engine(app=current_app, bind='func_stats').execute(
                FuncStat.__table__.insert(), func_stat
            )

        # although we have defined models to enable cascased delete operation,
        # it actually didn't work. The reason is that we do the bulk insertion
        # to get performance and, for now, I couldn't figure out how to define
        # backreference in the above bulk insertion. So that, we do delete
        # Stat rows manually (but using bulk deletion)

        # currently this is error prone!!!

        # delete_old_anomaly()
        # delete_old_func()
    except Exception as e:
        print(e)

    try:
        # get query condition from database
        q = AnomalyStatQuery.query. \
            order_by(AnomalyStatQuery.created_at.desc()).first()

        if q is None:
            q = AnomalyStatQuery.create({
                'nQueries': 5,
                'statKind': 'stddev',
                'ranks': []
            })
            db.session.add(q)
            db.session.commit()

        if len(anomaly_stat):
            push_anomaly_stat(q, anomaly_stat, anomaly_counters)

        if len(anomaly_data):
            push_anomaly_data(q, anomaly_data)

    except Exception as e:
        print(e)

    # todo: make information output with Location
    return jsonify({}), 201


@api.route('/anomalystats', methods=['GET'])
def new_anomalystats():
    """Push model to query and broadcast current query condition
    data to the front end client
    """
    # get query condition from database
    query = AnomalyStatQuery.query. \
        order_by(AnomalyStatQuery.created_at.desc()).first()

    if query is None:
        query = AnomalyStatQuery.create({
            'nQueries': 5,
            'statKind': 'stddev',
            'ranks': []
        })
        db.session.add(query)
        db.session.commit()

    subq = db.session.query(
        AnomalyStat.app,
        AnomalyStat.rank,
        func.max(AnomalyStat.created_at).label('max_ts')
    ).group_by(AnomalyStat.app, AnomalyStat.rank).subquery('t2')

    stats = db.session.query(AnomalyStat).join(
        subq,
        and_(
            AnomalyStat.app == subq.c.app,
            AnomalyStat.rank == subq.c.rank,
            AnomalyStat.created_at == subq.c.max_ts
        )
    ).all()

    push_anomaly_stat(query, [st.to_dict() for st in stats], [])
    return jsonify({}), 200


@api.route('/run_simulation', methods=['GET'])
@make_async
def run_simulation():
    import time
    import glob

    error = 'OK'
    path = os.environ.get('SIMULATION_JSON', 'json/')
    json_files = glob.glob(path + '*.json')
    # extract number as index
    ids = [int(f.split('_')[-1][:-5]) for f in json_files]
    # sort as numeric values
    inds = sorted(range(len(ids)), key=lambda k: ids[k])
    files = [json_files[i] for i in inds]  # files in correct order

    # clean up db before the simulation
    # delete_all_db()

    try:
        for filename in files:
            # print("File {} out of {} files.".format(filename, len(files)))
            data = None
            with open(filename) as f:
                loaded = json.load(f)
                data = loaded.get('anomaly_stats', None)
                counter_stats = loaded.get('counter_stats', None)

            if data is None:
                time.sleep(0.2)
                continue

            ts = data.get('created_at', None)
            if ts is None:
                abort(400)

            # process counter stats
            anomaly_counters = []
            cpu_counters = ['cpu: User %',
                            'cpu: Idle %',
                            'cpu: System %']
            gpu_counters = ['GPU Occupancy (Warps)',
                            'Local Memory (bytes per thread)',
                            'Shared Static Memory (bytes)']
            if counter_stats:
                for d in counter_stats:
                    if d['counter'] in gpu_counters or \
                       d['counter'] in cpu_counters:
                        anomaly_counters.append(d)

            # print('processing...')
            anomaly_stat, anomaly_data = \
                process_on_anomaly(data.get('anomaly', []), ts)
            func_stat = process_on_func(data.get('func', []), ts)

            # print('update db...')
            try:
                if len(anomaly_stat):
                    db.get_engine(app=current_app,
                                  bind='anomaly_stats').execute(
                        AnomalyStat.__table__.insert(), anomaly_stat
                    )
                    db.get_engine(app=current_app,
                                  bind='anomaly_data').execute(
                        AnomalyData.__table__.insert(), anomaly_data
                    )
                if len(func_stat):
                    db.get_engine(app=current_app, bind='func_stats').execute(
                        FuncStat.__table__.insert(), func_stat
                    )

            except Exception as e:
                print(e)

            q = AnomalyStatQuery.query. \
                order_by(AnomalyStatQuery.created_at.desc()).first()

            if q is None:
                q = AnomalyStatQuery.create({
                    'nQueries': 5,
                    'statKind': 'stddev',
                    'ranks': []
                })
                db.session.add(q)
                db.session.commit()

            # print("ts: {}, data: {}", ts, len(data))
            if len(anomaly_stat):
                push_anomaly_stat(q, anomaly_stat, anomaly_counters)

            if len(anomaly_data):
                push_anomaly_data(q, anomaly_data)

            time.sleep(1)
    except Exception as e:
        print('Exception on run simulation: ', e)
        error = 'exception while running simulation'
        pass

    push_data({'result': error}, 'run_simulation')

    return jsonify({}), 200


@api.route('/get_anomalystats', methods=['GET'])
def get_anomalystats():
    """
    Return anomaly stat specified by app and rank index
    - (e.g.) /api/get_anomalystats will return all available statistics
    - (e.g.) /api/get_anomalystats?app=0&rank=0 will return statistics of
                 application index is 0 and rank index is 0.
    - return 400 error if there are no available statistics
    """
    app = request.args.get('app', default=None)
    rank = request.args.get('rank', default=None)

    stats = AnomalyStat.query.filter(
        and_(
            AnomalyStat.app == int(app),
            AnomalyStat.rank == int(rank),
        )
    ).all()

    push_anomaly_stat(query, [st.to_dict() for st in stats], [])
    # return jsonify({}), 200
    return jsonify([st.to_dict() for st in stats])


@api.route('/get_anomalydata', methods=['GET'])
def get_anomalydata():
    app = request.args.get('app', default=None)
    rank = request.args.get('rank', default=None)

    data = AnomalyData.query.filter(
        and_(
            AnomalyData.app == int(app),
            AnomalyData.rank == int(rank)
        )
    ).order_by(
        AnomalyData.step.desc()
    ).all()

    data.reverse()

    return jsonify([dd.to_dict() for dd in data])


@api.route('/get_funcstats', methods=['GET'])
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
