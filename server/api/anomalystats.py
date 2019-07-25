from flask import request, abort, jsonify

from .. import db
from ..models import AnomalyStat

from . import api


@api.route('/anomalystats', methods=['POST'])
def new_anomalystats():
    payload = request.get_json()

    stat = AnomalyStat.create(payload)

    db.session.merge(stat)
    db.session.commit()

    return "OK"


@api.route('/anomalystats/<int:id>', methods=['GET'])
def get_anomalystats(id):
    pass
