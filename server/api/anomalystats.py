from flask import request, jsonify

from .. import db
from ..models import AnomalyStat
from . import api
from ..tasks import make_async
from ..utils import url_for


@api.route('/anomalystats', methods=['POST'])
@make_async
def new_anomalystats():
    """Register new anaomaly stats"""
    payload = request.get_json() or {}
    stat = AnomalyStat.create(payload)

    db.session.merge(stat)
    db.session.commit()

    r = jsonify({})
    r.status_code = 201
    r.headers['Location'] = url_for('api.get_anomalystats', id=stat.id)
    return r


@api.route('/anomalystats/<int:id>', methods=['GET'])
def get_anomalystats(id):
    """Return anomaly stat specified by id"""
    return jsonify(AnomalyStat.query.get_or_404(id).to_dict())
