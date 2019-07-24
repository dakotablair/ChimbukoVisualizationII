from flask import request, abort, jsonify

from .. import db
from ..models import Execution

from . import api


@api.route('/executions', methods=['POST'])
def new_executions():
    """Register a list of new executions"""
    all_exec = [Execution.create(d) for d in request.get_json()]
    db.session.add_all(all_exec)
    db.session.commit()
    return "OK"


@api.route('/execution', methods=['POST'])
def new_execution():
    """Register new executions"""
    _exec = Execution.create(request.get_json()) or {}
    if Execution.query.filter_by(id=_exec.id).first() is not None:
        abort(400)
    db.session.add(_exec)
    db.session.commit()
    return "OK"


@api.route('/execution/<id>', methods=['GET'])
def get_execution(id):
    """Return execution data specified by id"""
    _exec = Execution.query.filter_by(id=id).first()
    if _exec is None:
        abort(400)
    return jsonify(_exec.to_dict())


@api.route('/executions', methods=['GET'])
def get_executions():
    """
    Return a list of execution data
    - options
        time: [(t_entry) | t_exit | t_runtime]
        order: [(asc) | desc]
        filter_by: [(label)]
        since: default 0
        until
    """
    col = Execution.t_entry
    if request.args.get('time'):
        if request.args.get('time') == 't_exit':      col = Execution.t_exit
        elif request.args.get('time') == 't_runtime': col = Execution.t_runtime

    o = request.args.get('order', default='asc')
    if o == 'asc':
        all_exec = Execution.query.order_by(col.asc())
    else:
        all_exec = Execution.query.order_by(col.desc())

    if all_exec is None:
        abort(400)

    if request.args.get('label', default=None) is not None:
        all_exec = all_exec.filter_by(label=int(request.args.get('label')))

    if request.args.get('since', default=None) is not None:
        all_exec = all_exec.filter(col >= int(request.args.get('since')))

    if request.args.get('until', default=None) is not None:
        all_exec = all_exec.filter(col <= int(request.args.get('until')))

    return jsonify([d.to_dict() for d in all_exec.all()])
