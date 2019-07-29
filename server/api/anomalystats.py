from flask import request, abort, jsonify

from .. import db
from ..models import AnomalyStat

from . import api


@api.route('/anomalystats', methods=['POST'])
def new_anomalystats():
    """Register new anaomaly stats"""
    payload = request.get_json()

    stat = AnomalyStat.create(payload)

    db.session.merge(stat)
    db.session.commit()

    return "OK"


@api.route('/anomalystats/<int:id>', methods=['GET'])
def get_anomalystats(id):
    """Return anomaly stat specified by id"""
    stat = AnomalyStat.query.filter_by(id=id).first()
    if stat is None:
        abort(400)
    return jsonify(stat.to_dict())
