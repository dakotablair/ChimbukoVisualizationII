from flask import Flask
from flask_sqlalchemy import SQLAlchemy

#####
from server.utils import timestamp
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import backref
####


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'

db = SQLAlchemy(app)

### models
class Base(db.Model):
    __abstract__ = True
    id = db.Column(INTEGER(unsigned=True), primary_key=True)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    # unique key
    key = db.Column(db.String(), unique=True)

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
    funcstat_key = db.Column(db.String(), db.ForeignKey('funcstat.key'))
    anomalystat_key = db.Column(db.String(), db.ForeignKey('anomalystat.key'))

    kind = db.Column(db.String(), default='default')

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


class AnomalyData(Base):
    __tablename__ = 'anomalydata'
    anomalystat_key = db.Column(db.String(), db.ForeignKey('anomalystat.key'))

    # step & the number of detected anomalies
    n_anomaly = db.Column(db.Integer, default=0)
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
    anomalystat_key = db.Column(db.String(), db.ForeignKey('execdata.key'))

    src = db.Column(db.Integer, default=0)
    dst = db.Column(db.Integer, default=0)
    size = db.Column(db.Integer, default=0) # in bytes
    tag = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.Integer, default=0) # usec

### end models

