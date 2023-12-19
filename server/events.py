import os
from flask import g, session, Blueprint, current_app, request
from flask import jsonify, abort, json

from . import db, socketio, celery, pdb
from .models import AnomalyStat, AnomalyData, AnomalyStatQuery
# from .models import ExecData, CommData

from sqlalchemy import func, and_

from .tasks import make_async

import pymargo
from pymargo.core import Engine
from pysonata.provider import SonataProvider
from pysonata.client import SonataClient
from pysonata.admin import SonataAdmin

import random

events = Blueprint('events', __name__)


def push_data(data, event='updated_data',  namespace='/events'):
    """Push the data to all connected Socket.IO clients."""
    socketio.emit(event, data, namespace=namespace)


def load_execution_provdb(conditions):
    """Load execution data from provdb as unqlite file

    Assumption: must query by pid and io_steps at least, they could be -1,
    to return nothing
    """

    print("load_execution_provdb:", conditions)

    filtered_records = []
    pid, rid, step1, step2, fid, severity, score = conditions[0], \
        conditions[1], conditions[2], conditions[3], conditions[4], \
        conditions[5], conditions[6]
    # collection = pdb.open('anomalies')  # default collection
    jx9_filter = None
    if rid:  # query by rank
        if not fid:  # only by rank and io_steps
            if severity and score:
                jx9_filter = "function($record) { return " \
                    "$record.pid == %d && " \
                    "$record.rid == %d && " \
                    "$record.io_step >= %d && " \
                    "$record.io_step <= %d && " \
                    "$record.outlier_severity >= %f && " \
                    "$record.outlier_score >= %f;} " % (int(pid),
                                                        int(rid),
                                                        int(step1),
                                                        int(step2),
                                                        float(severity)*1000,
                                                        float(score))
            elif severity and not score:
                jx9_filter = "function($record) { return " \
                    "$record.pid == %d && " \
                    "$record.rid == %d && " \
                    "$record.io_step >= %d && " \
                    "$record.io_step <= %d && " \
                    "$record.outlier_severity >= %f;} " % (int(pid),
                                                           int(rid),
                                                           int(step1),
                                                           int(step2),
                                                           float(severity)*1000)
            elif not severity and score:
                jx9_filter = "function($record) { return " \
                    "$record.pid == %d && " \
                    "$record.rid == %d && " \
                    "$record.io_step >= %d && " \
                    "$record.io_step <= %d && " \
                    "$record.outlier_score >= %f;} " % (int(pid),
                                                        int(rid),
                                                        int(step1),
                                                        int(step2),
                                                        float(score))
            else:
                jx9_filter = "function($record) { return " \
                    "$record.pid == %d && " \
                    "$record.rid == %d && " \
                    "$record.io_step >= %d && " \
                    "$record.io_step <= %d;} " % (int(pid),
                                                  int(rid),
                                                  int(step1),
                                                  int(step2))
        else:  # query by rank and fid and io_steps
            if severity and score:
                jx9_filter = "function($record) { return " \
                    "$record.pid == %d && " \
                    "$record.rid == %d && " \
                    "$record.fid == %d && " \
                    "$record.io_step >= %d && " \
                    "$record.io_step <= %d && " \
                    "$record.outlier_severity >= %f && " \
                    "$record.outlier_score >= %f;} " % (int(pid),
                                                        int(rid),
                                                        int(fid),
                                                        int(step1),
                                                        int(step2),
                                                        float(severity)*1000,
                                                        float(score))
            elif severity and not score:
                jx9_filter = "function($record) { return " \
                    "$record.pid == %d && " \
                    "$record.rid == %d && " \
                    "$record.fid == %d && " \
                    "$record.io_step >= %d && " \
                    "$record.io_step <= %d && " \
                    "$record.outlier_severity >= %f;} " % (int(pid),
                                                           int(rid),
                                                           int(fid),
                                                           int(step1),
                                                           int(step2),
                                                           float(severity)*1000)
            elif not severity and score:
                jx9_filter = "function($record) { return " \
                    "$record.pid == %d && " \
                    "$record.rid == %d && " \
                    "$record.fid == %d && " \
                    "$record.io_step >= %d && " \
                    "$record.io_step <= %d && " \
                    "$record.outlier_score >= %f;} " % (int(pid),
                                                        int(rid),
                                                        int(fid),
                                                        int(step1),
                                                        int(step2),
                                                        float(score))
            else:
                jx9_filter = "function($record) { return " \
                    "$record.pid == %d && " \
                    "$record.rid == %d && " \
                    "$record.fid == %d && " \
                    "$record.io_step >= %d && " \
                    "$record.io_step <= %d;} " % (int(pid),
                                                  int(rid),
                                                  int(fid),
                                                  int(step1),
                                                  int(step2))
    else:  # rank is unknown
        if fid:  # query by fid and io_steps
            if severity and score:
                jx9_filter = "function($record) { return " \
                    "$record.pid == %d && " \
                    "$record.fid == %d && " \
                    "$record.io_step >= %d && " \
                    "$record.io_step <= %d && " \
                    "$record.outlier_severity >= %f && " \
                    "$record.outlier_score >= %f;} " % (int(pid),
                                                  int(fid),
                                                  int(step1),
                                                  int(step2),
                                                  float(severity)*1000,
                                                  float(score))
            elif severity and not score:
                jx9_filter = "function($record) { return " \
                    "$record.pid == %d && " \
                    "$record.fid == %d && " \
                    "$record.io_step >= %d && " \
                    "$record.io_step <= %d && " \
                    "$record.outlier_severity >= %f;} " % (int(pid),
                                                           int(fid),
                                                           int(step1),
                                                           int(step2),
                                                           float(severity)*1000)
            elif not severity and score:
                jx9_filter = "function($record) { return " \
                    "$record.pid == %d && " \
                    "$record.fid == %d && " \
                    "$record.io_step >= %d && " \
                    "$record.io_step <= %d && " \
                    "$record.outlier_score >= %f;} " % (int(pid),
                                                        int(fid),
                                                        int(step1),
                                                        int(step2),
                                                        float(score))
            else:
                jx9_filter = "function($record) { return " \
                    "$record.pid == %d && " \
                    "$record.fid == %d && " \
                    "$record.io_step >= %d && " \
                    "$record.io_step <= %d;} " % (int(pid),
                                                  int(fid),
                                                  int(step1),
                                                  int(step2))
        else:  # both rank and fid are unknown
            print("Error: requires at least one of [rid, fid]")
            return filtered_records

    if pdb and pdb.pdb_collections:
        for col in pdb.pdb_collections:
            result = [json.loads(x) for x in col.filter(jx9_filter)]
            filtered_records += result
    n = len(filtered_records)
    print("{} records from provdb, returned {}".format(n,
                                                       n if n <= 100 else 100))

    # gpu_count = 0
    # for record in filtered_records:  # reduced_records:
    #     if record['is_gpu_event']:
    #         gpu_count += 1
    # print("...{} are gpu events...".format(gpu_count))

    return filtered_records[:100]  # reduced_records


@events.route('/query_executions_pdb', methods=['GET'])
def get_execution_pdb():
    """
    Return a list of execution data within a given time range
        pid: program index
        rid: [rank index]
        step1: lower io_step index
        step2: upper io_step index
        fid: [function index]
        severity: [outlier_severity (execution time)]
        score: [outlier_score (algorithm score, whether is anomaly)]
        order: [(asc) | desc]
    """
    conditions = []
    attrs = ['pid', 'rid', 'step1', 'step2', 'fid', 'severity', 'score']
    for attr in attrs:
        conditions.append(request.args.get(attr, None))
        if conditions[-1] and int(conditions[-1]) == -1:
            conditions[-1] = None

    if all(v is None for v in conditions):
        abort(400)

    print("queried: ", conditions)

    # parse options
    order = request.args.get('order', 'asc')

    execdata = []
    execdata = load_execution_provdb(conditions)
    sort_desc = order == 'desc'
    execdata.sort(key=lambda d: d['entry'], reverse=sort_desc)

    return jsonify({"exec": execdata})
    # return jsonify(execdata), 200


@socketio.on('query_stats', namespace='/events')
def query_stats(q):
    nQueries = q.get('nQueries', 5)
    statKind = q.get('statKind', 'stddev')
    ranks = q.get('ranks', [])

    q = AnomalyStatQuery.create({
        'nQueries': nQueries,
        'statKind': statKind,
        'ranks': ranks
    })
    db.session.add(q)
    db.session.commit()


@socketio.on('connect', namespace='/events')
def events_connect():
    print('socketio.on.connect')


@socketio.on('disconnect', namespace='/events')
def events_disconnect():
    print('socketio.on.disconnect')

