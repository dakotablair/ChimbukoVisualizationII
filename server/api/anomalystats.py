from flask import request, jsonify, abort

from .. import db
from ..models import AnomalyStat, AnomalyData
from . import api
from ..tasks import make_async
# from ..utils import url_for

from sqlalchemy.exc import IntegrityError
from runstats import Statistics
from collections import defaultdict


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
    curr_stats = AnomalyStat.query.filter_by(app=app, rank=rank).first()

    # An AnomalyStat object doesn't exist, then create new one
    if curr_stats is None:
        curr_stats = AnomalyStat.create_from(app, rank, stats)
        db.session.begin_nested()
        try:
            db.session.add(curr_stats)
            db.session.commit()
        except IntegrityError:
            # The insert fail due to a concurrent transaction
            db.session.rollback()
            curr_stats = create_or_update_stats(app, rank, stats)
        return curr_stats

    curr_key = curr_stats.key
    st = curr_stats.to_stats()
    st += stats

    (_count, _eta, _rho, _tau, _phi, _min, _max) = st.get_state()
    new_key = '{}:{}:{}'.format(app, rank, int(curr_key.split(':')[-1]) + 1)

    curr_stats.key = new_key
    curr_stats.count = _count
    curr_stats.eta = _eta
    curr_stats.rho = _rho
    curr_stats.tau = _tau
    curr_stats.phi = _phi
    curr_stats.min = _min
    curr_stats.max = _max

    db.session.begin_nested()
    try:
        db.session.commit()
    except IntegrityError:
        # The update fails due to a concurrent transaction
        db.session.rollback()
        curr_stats = create_or_update_stats(app, rank, stats)

    return curr_stats


@api.route('/anomalydata', methods=['POST'])
@make_async
def new_anomalydata():
    """Register list of anomaly data"""
    payload = request.get_json() or {}
    if not isinstance(payload, list):
        payload = [payload]

    # compute local statistics with given anomaly data list
    l_stats = defaultdict(lambda: Statistics())
    for d in payload:
        l_stats[d['app_rank']].push(d['n'])

    # create or update AnomalyStat table
    g_stats = {}
    for app_rank, stats in l_stats.items():
        app, rank = app_rank.split(':')
        g_stats[app_rank] = create_or_update_stats(int(app), int(rank), stats)
    # For some reason, I need to commit again here... why??
    db.session.commit()

    # This is about x30 times faster than db.session.add_all method
    for data in payload:
        data['stat_id'] = g_stats[data['app_rank']].id
    db.engine.execute(AnomalyData.__table__.insert(), payload)

    return jsonify({}), 201


@api.route('/anomalystats/<int:id>', methods=['GET'])
def get_anomalystat(id):
    """Return anomaly stat specified by id"""
    return jsonify(AnomalyStat.query.get_or_404(id).to_dict())


@api.route('/anomalystats', methods=['GET'])
def get_anomalystats():
    print('get_anomalystats')
    stats = AnomalyStat.query.order_by(AnomalyStat.id.asc())
    print([d.to_dict() for d in stats.all()])
    if stats is None:
        abort(400)

    return jsonify([d.to_dict() for d in stats.all()])
