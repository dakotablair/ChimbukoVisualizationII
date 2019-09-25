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
            'key': self.key,
            'key_ts': self.key_ts,
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
        d = super().to_dict()

        stats = {}
        for st in self.stats.all():
            stats[st.kind] = st.to_dict()

        d.update({
            'fid': self.fid,
            'name': self.name,
            **stats
        })
        return d


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
        backref=backref('anomaly', cascade="all,delete")
    )

    # anomaly data for history view
    # - anomaly data history
    # - one-to-many, no cascaded operation
    hist = db.relationship('AnomalyData', lazy='dynamic', backref='owner')

    def to_dict(self):
        d = super().to_dict()

        d.update({
            'app': self.app,
            'rank': self.rank,
            'stats': self.stat.to_dict()
        })
        return d


class Stat(Base):
    __tablename__ = 'stat'
    funcstat_key = db.Column(db.String(), db.ForeignKey('funcstat.key_ts'), nullable=True)
    anomalystat_key = db.Column(db.String(), db.ForeignKey('anomalystat.key_ts'), nullable=True)

    kind = db.Column(db.String(), default='anomaly')

    count = db.Column(db.Integer, default=0)
    accumulate = db.Column(db.Integer, default=0)
    minimum = db.Column(db.Integer, default=0)
    maximum = db.Column(db.Integer, default=0)
    mean = db.Column(db.Integer, default=0)
    stddev = db.Column(db.Integer, default=0)
    skewness = db.Column(db.Integer, default=0)
    kurtosis = db.Column(db.Integer, default=0)

    def to_dict(self):
        d = super().to_dict()
        d.update({
            'kind': self.kind,
            'count': self.count,
            'accumulate': self.accumulate,
            'minimum': self.minimum,
            'maximum': self.maximum,
            'mean': self.mean,
            'stddev': self.stddev,
            'skewness': self.skewness,
            'kurtosis': self.kurtosis
        })
        return d


class AnomalyData(Base):
    __tablename__ = 'anomalydata'
    anomalystat_key = db.Column(db.String(), db.ForeignKey('anomalystat.key'))

    # step & the number of detected anomalies
    n_anomalies = db.Column(db.Integer, default=0)
    step = db.Column(db.Integer, index=True, default=0)
    min_timestamp = db.Column(db.Float, default=0)  # usec
    max_timestamp = db.Column(db.Float, default=0)  # usec

    def to_dict(self):
        d = super().to_dict()
        d.update({
            'anomalystat_key': self.anomalystat_key,
            'n_anomalies': self.n_anomalies,
            'step': self.step,
            'min_timestamp': self.min_timestamp,
            'max_timestamp': self.max_timestamp
        })
        return d


class ExecData(Base):
    __tablename__ = 'execdata'

    pid = db.Column(db.Integer, default=0)
    rid = db.Column(db.Integer, default=0)
    tid = db.Column(db.Integer, default=0)

    fid = db.Column(db.Integer, default=0)
    name = db.Column(db.String(), default="unknown")

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
    comm = db.relationship(
        'CommData', lazy='dynamic',
        cascade='all,delete-orphan',
        single_parent=True,
        backref=backref('exec', cascade="all"))

    def to_dict(self, with_comm=0):
        d = super().to_dict()
        d.update({
            'pid': self.pid,
            'rid': self.rid,
            'tid': self.tid,
            'fid': self.fid,
            'name': self.name,
            'entry': self.entry,
            'exit': self.exit,
            'runtime': self.runtime,
            'exclusive': self.exclusive,
            'label': self.label,
            'parent': self.parent,
            'n_children': self.n_children,
            'n_messages': self.n_messages
        })
        if int(with_comm) > 0:
            d.update({
                'comm': [c.to_dict() for c in self.comm.all()]
            })
        return d


class CommData(Base):
    __tablename__ = 'commdata'
    execdata_key = db.Column(db.String(), db.ForeignKey('execdata.key'))

    type = db.Column(db.String())
    src = db.Column(db.Integer, default=0)
    tar = db.Column(db.Integer, default=0)
    size = db.Column(db.Integer, default=0)  # in bytes
    tag = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.Integer, default=0)  # usec

    def to_dict(self):
        d = super().to_dict()
        d.update({
            'execdata_key': self.execdata_key,
            'type': self.type,
            'src': self.src,
            'tar': self.tar,
            'size': self.size,
            'tag': self.tag,
            'timestamp': self.timestamp
        })
        return d
