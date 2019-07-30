from flask import request, jsonify, abort

from .. import db
from ..models import AnomalyStat
from . import api
from ..tasks import make_async
# from ..utils import url_for


@api.route('/anomalystats', methods=['POST'])
@make_async
def new_anomalystats():
    """Register new anaomaly stats"""
    payload = request.get_json() or {}
    if not isinstance(payload, list):
        payload = [payload]

    try:
        for d in payload:
            stat = AnomalyStat.create(d)
            db.session.merge(stat)
            db.session.commit()
    except Exception as e:
        print('error: ', e)

    # r = jsonify({})
    # r.status_code = 201
    # r.headers['Location'] = url_for('api.get_anomalystats', id=stat.id)
    return jsonify({}), 201


@api.route('/anomalystats/<int:id>', methods=['GET'])
def get_anomalystat(id):
    """Return anomaly stat specified by id"""
    return jsonify(AnomalyStat.query.get_or_404(id).to_dict())


@api.route('/anomalystats', methods=['GET'])
def get_anomalystats():
    stats = AnomalyStat.query.all()
    if stats is None:
        abort(400)
    return jsonify([d.to_dict() for d in stats])
