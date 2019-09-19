from flask import abort
from . import db
from .utils import timestamp
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import backref


class AnomalyStatQuery(db.Model):
    __tablename__ = 'anomalystatquery'
    id = db.Column(INTEGER(unsigned=True), primary_key=True)

    nQueries = db.Column(db.Integer, default=0)
    statKind = db.Column(db.String(), default='stddev')

    created_at = db.Column(db.Integer, index=True, default=timestamp)

    @staticmethod
    def create(data):
        """Create a new Query condition"""
        q = AnomalyStatQuery()
        q.from_dict(data)
        return q

    def from_dict(self, data: dict, partial_update=False):
        """Import from a dictionary"""
        for field in data.keys():
            try:
                setattr(self, field, data[field])
            except KeyError:
                if not partial_update:
                    abort(400)

    def to_dict(self):
        """Export to a dictionary"""
        return {
            'id': self.id,
            'nQueries': self.nQueries,
            'statKind': self.statKind,
            'crreated_at': self.created_at
        }


class Base(db.Model):
    __abstract__ = True
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # key
    key = db.Column(db.String())
    key_ts = db.Column(db.String())

    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class FuncStat(Base):
    __tablename__ = 'funcstat'
    fid = db.Column(db.Integer)
    name = db.Column(db.String())

    # statistics
    # - anomaly, inclusive, exclusive
    # - one-to-many, cascaded delete, delete-orphan
    stats = db.relationship(
        'Stat', lazy='dynamic',
        cascade='all,delete-orphan',
        single_parent=True,
        backref=backref('func', cascade="all"))

    def to_dict(self):
        return super().to_dict().update({
            'fid': self.fid,
            'name': self.name
        })


class AnomalyStat(Base):
    __tablename__ = 'anomalystat'

    # application & rank id's
    app = db.Column(db.Integer, default=0)  # application id
    rank = db.Column(db.Integer, default=0)  # rank id

    # statistics
    # - anomaly
    # - one-to-one, cascaded delete, delete-orphan
    stat = db.relationship(
        'Stat',
        cascade='all,delete-orphan',
        single_parent=True,
        uselist=False,
        backref=backref('anomaly', cascade="all")
    )

    # anomaly data for history view
    # - anomaly data history
    # - one-to-many, no cascaded operation
    hist = db.relationship('AnomalyData', lazy='dynamic', backref='owner')


class Stat(Base):
    __tablename__ = 'stat'
    funcstat_key = db.Column(db.String(), db.ForeignKey('funcstat.key_ts'))
    anomalystat_key = db.Column(db.String(), db.ForeignKey('anomalystat.key_ts'))

    # kind = db.Column(db.String(), default='default')

    count = db.Column(db.Integer, default=0)
    accumulate = db.Column(db.Integer, default=0)
    minimum = db.Column(db.Integer, default=0)
    maximum = db.Column(db.Integer, default=0)
    mean = db.Column(db.Integer, default=0)
    stddev = db.Column(db.Integer, default=0)
    skewness = db.Column(db.Integer, default=0)
    kurtosis = db.Column(db.Integer, default=0)

    def to_dict(self):
        return super().to_dict().update({
            # 'kind': self.kind,
            'count': self.count,
            'acc': self.accumulate,
            'min': self.minimum,
            'max': self.maximum,
            'mean': self.mean,
            'stddev': self.stddev,
            'skewness': self.skewness,
            'kurtosis': self.kurtosis
        })


class AnomalyData(Base):
    __tablename__ = 'anomalydata'
    anomalystat_key = db.Column(db.String(), db.ForeignKey('anomalystat.key'))

    # step & the number of detected anomalies
    n_anomalies = db.Column(db.Integer, default=0)
    step = db.Column(db.Integer, index=True, default=0)
    min_timestamp = db.Column(db.Float, default=0)  # usec
    max_timestamp = db.Column(db.Float, default=0)  # usec


class ExecData(Base):
    __tablename__ = 'execdata'

    pid = db.Column(db.Integer, default=0)
    rid = db.Column(db.Integer, default=0)
    tid = db.Column(db.Integer, default=0)

    fid = db.Column(db.Integer, default=0)
    fname = db.Column(db.String(), default="unknown")

    entry = db.Column(db.Float, default=0)
    exit = db.Column(db.Float, default=0)
    runtime = db.Column(db.Float, default=0)
    exclusive = db.Column(db.Float, default=0)

    label = db.Column(db.Integer, default=0)

    parent = db.Column(db.String(), default='root')
    n_children = db.Column(db.Integer, default=0)
    n_messages = db.Column(db.Integer, default=0)

    # communication
    # - one-to-many, cascaded delete, delete-orphan
    stats = db.relationship(
        'CommData', lazy='dynamic',
        cascade='all,delete-orphan',
        single_parent=True,
        backref=backref('exec', cascade="all"))


class CommData(Base):
    __tablename__ = 'commdata'
    execdata_key = db.Column(db.String(), db.ForeignKey('execdata.key'))

    type = db.Column(db.String())
    src = db.Column(db.Integer, default=0)
    tar = db.Column(db.Integer, default=0)
    size = db.Column(db.Integer, default=0)  # in bytes
    tag = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.Integer, default=0)  # usec


# class ApplicationInfo(db.Model):
#     __tablename__ = 'appinfo'
#     id = db.Column(INTEGER(unsigned=True), primary_key=True)
#
#     # application id & name & # MPI ranks
#     # - application id should be matched with anomalystat.app
#     # - todo: foreign key
#     app_id = db.Column(db.Integer, default=0)
#     app_name = db.Column(db.String())
#     app_rank = db.Column(db.Integer, default=0)
#
#     # belows are user dependent
#     # - this is only for now because this is valid only for single user
#     order_by = db.Column(db.String(), default="stddev")
#     n_query = db.Column(db.Integer, default=5)
#
#     # timestamps
#     created_at = db.Column(db.Integer, default=timestamp)
#     updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
#
#     @staticmethod
#     def create(data):
#         """Create an application information"""
#         info = ApplicationInfo(
#             app_id=0, app_name="unknown", app_rank=0,
#             order_by="stddev", n_query=5
#         )
#         info.from_dict(data)
#         return info
#
#     def from_dict(self, data: dict, partial_update=True):
#         """Import application information from a dictionary"""
#         for field in data.keys():
#             try:
#                 setattr(self, field, data[field])
#             except KeyError:
#                 if not partial_update:
#                     abort(400)
#
#     def to_dict(self):
#         """Export application information to a dictionary"""
#         return {
#             'id': self.id,
#             'app_id': self.app_id,
#             'app_name': self.app_name,
#             'app_rank': self.app_rank,
#             'order_by': self.order_by,
#             'n_query': self.n_query,
#             'created_at': self.created_at,
#             'updated_at': self.updated_at
#         }
#
#
# class AnomalyStat(db.Model):
#     """
#     Anomaly statistics
#     - contains internal state of Statistics object
#     """
#     __tablename__ = 'anomalystat'
#     id = db.Column(INTEGER(unsigned=True), primary_key=True)
#
#     # application & rank id's
#     app = db.Column(db.Integer, default=0)  # application id
#     rank = db.Column(db.Integer, default=0)  # rank id
#
#     # timestamp
#     created_at = db.Column(db.Integer, index=True, default=timestamp)
#
#     # for references between AnomalyStat and AnomalyData
#     key = db.Column(db.String())
#
#     # statistics
#     # - n_updates: the number of updates (equivalent to the number of steps)
#     # - n_anomalies: the number of accumulated anomalies
#     # - n_min_anomalies: the minimum number of anomalies
#     # - n_max_anomalies: the maximum number of anomalies
#     # - mean: mean of number of anomalies over time (or steps)
#     # - stddev: std. dev. of number of anomalies over time (or steps)
#     # - skewness: skewness of number of anomalies over time
#     # - kurtosis: kurtosis of number of anomalies over time
#     n_updates = db.Column(db.Integer, default=0)
#     n_anomalies = db.Column(db.Integer, default=0)
#     n_min_anomalies = db.Column(db.Integer, default=0)
#     n_max_anomalies = db.Column(db.Integer, default=0)
#     mean = db.Column(db.Float, default=0)
#     stddev = db.Column(db.Float, default=0)
#     skewness = db.Column(db.Float, default=0)
#     kurtosis = db.Column(db.Float, default=0)
#
#     # reference to associated data
#     data = db.relationship('AnomalyData', lazy='dynamic', backref='owner')
#
#     def __repr__(self):
#         return '<AnomalyStat {}:{}:{}>'.format(
#             self.app, self.rank, self.n_updates)
#
#     @staticmethod
#     def create(data):
#         """Create a new anomaly statistics"""
#         if not all(field in data for field in ('app', 'rank')):
#             abort(400, message="Missing application or rank indices")
#         stat = AnomalyStat(
#             n_updates=0, n_anomalies=0, n_min_anomalies=0, n_max_anomalies=0,
#             mean=0, stddev=0, skewness=0, kurtosis=0
#         )
#         stat.from_dict(data, partial_update=True)
#         return stat
#
#     def from_dict(self, data, partial_update=True):
#         """Import anomaly statistics from a dictionary"""
#         for field in data.keys():
#             try:
#                 setattr(self, field, data[field])
#             except KeyError:
#                 if not partial_update:
#                     abort(400)
#
#         if 'key' not in data:
#             setattr(self, 'key', '{}:{}'.format(
#                 data['app'], data['rank']
#             ))
#
#     def to_dict(self):
#         """Export anomaly statistics to a dictionary"""
#         return {
#             'id': self.id,
#             'app': self.app,
#             'rank': self.rank,
#             'created_at': self.created_at,
#             'key': self.key,
#             'n_updates': self.n_updates,
#             'n_anomalies': self.n_anomalies,
#             'n_min_anomalies': self.n_min_anomalies,
#             'n_max_anomalies': self.n_max_anomalies,
#             'mean': self.mean,
#             'stddev': self.stddev,
#             'skewness': self.skewness,
#             'kurtosis': self.kurtosis
#         }
#
#
# class AnomalyData(db.Model):
#     """
#     Anomaly data
#     """
#     __tablename__ = 'anomalydata'
#     id = db.Column(INTEGER(unsigned=True), primary_key=True)
#
#     # step & the number of detected anomalies
#     n_anomaly = db.Column(db.Integer, default=0)
#     step = db.Column(db.Integer, index=True, default=0)
#     min_timestamp = db.Column(db.Float, default=0)  # milli-second
#     max_timestamp = db.Column(db.Float, default=0)  # milli-second
#
#     # key to statistics
#     stat_id = db.Column(db.Integer, db.ForeignKey('anomalystat.key'))
#
#     def __repr__(self):
#         return '<AnomalyData {}:{}>'.format(self.step, self.n_anomaly)
#
#     @staticmethod
#     def create(data, owner):
#         """Create a new anomaly data"""
#         d = AnomalyData(step=0, n=0, owner=owner)
#         d.from_dict(data, partial_update=True)
#         return d
#
#     def from_dict(self, data, partial_update=True):
#         """Import anomaly statistics from a dictionary"""
#         for field in data.keys():
#             try:
#                 setattr(self, field, data[field])
#             except KeyError:
#                 if not partial_update:
#                     abort(400)
#
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'n_anomaly': self.n_anomaly,
#             'step': self.step,
#             'min_timestamp': self.min_timestamp,
#             'max_timestamp': self.max_timestamp,
#             'stat_id': self.stat_id
#         }
#
#
# class Execution(db.Model):
#     """The Execution model"""
#     __tablename__ = 'executions'
#     id = db.Column(db.String(), primary_key=True)
#     created_at = db.Column(db.Integer, default=timestamp)
#     updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
#
#     pid = db.Column(db.Integer, default=0)  # program id
#     rid = db.Column(db.Integer, default=0)  # rank id
#     tid = db.Column(db.Integer, default=0)  # thread id
#     fid = db.Column(db.Integer, default=0)  # function id
#
#     fname = db.Column(db.String(), default='Unknown')  # function name
#
#     label = db.Column(db.Integer, default=0)      # 1 is anomaly; otherwise 0
#     t_entry = db.Column(db.Integer, default=0)    # entry time
#     t_exit = db.Column(db.Integer, default=0)     # exit time
#     t_runtime = db.Column(db.Integer, default=0)  # run time (exit - entry)
#
#     # parent = db.relationship()
#
#     @staticmethod
#     def create(data):
#         """Create a new execution"""
#         _exec = Execution()
#         _exec.from_dict(data, partial_update=False)
#         return _exec
#
#     def from_dict(self, data: dict, partial_update=True):
#         """Import execution data from a dictionary"""
#         for field in data.keys():
#             try:
#                 setattr(self, field, data[field])
#             except KeyError:
#                 if not partial_update:
#                     abort(400)
#
#         if 't_runtime' not in data:
#             try:
#                 setattr(self, 't_runtime', data['t_exit'] - data['t_entry'])
#             except KeyError:
#                 abort(400)
#
#     def to_dict(self):
#         """Export execution data to a dictionary"""
#         return {
#             'id': self.id,
#             'created_at': self.created_at,
#             'updated_at': self.updated_at,
#             'pid': self.pid,
#             'rid': self.rid,
#             'tid': self.tid,
#             'fid': self.fid,
#             'fname': self.fname,
#             'label': self.label,
#             't_entry': self.t_entry,
#             't_exit': self.t_exit,
#             't_runtime': self.t_runtime
#         }
