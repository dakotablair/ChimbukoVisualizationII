from flask import abort
from . import db
from .utils import timestamp
from runstats import Statistics


class AnomalyStat(db.Model):
    """
    Anomaly statistics
    - contains internal state of Statistics object
    """
    __tablename__ = 'anomalystat'
    id = db.Column(db.Integer, primary_key=True)

    # application & rank id's
    app = db.Column(db.Integer, index=True, default=0)  # application id
    rank = db.Column(db.Integer, index=True, default=0)  # rank id

    # (unique) key for race-condition
    key = db.Column(db.String(), unique=True)

    # internal variables of Statistics object
    count = db.Column(db.Float, default=0)
    eta = db.Column(db.Float, default=0)
    rho = db.Column(db.Float, default=0)
    tau = db.Column(db.Float, default=0)
    phi = db.Column(db.Float, default=0)
    min = db.Column(db.Float, default=0)
    max = db.Column(db.Float, default=0)

    # reference to associated data
    data = db.relationship('AnomalyData', lazy='dynamic', backref='owner')

    def __repr__(self):
        stats = Statistics.fromstate(
            (self.count, self.eta, self.rho, self.tau, self.phi,
             self.min, self.max)
        )
        return '<AnomalyStat {}:{} count={}, ' \
               'min={:.3f}, max={:.3f} ' \
               'mean={:.3f}, stddev={:.3f}, ' \
               'skewness={:.3f}, kurtosis={:.3f}>'.format(
                   self.app, self.rank,
                   len(stats), stats.minimum(), stats.maximum(),
                   stats.mean(), stats.stddev(),
                   stats.skewness(), stats.kurtosis())

    @staticmethod
    def create(data):
        """Create a new anomaly statistics"""
        if not all(field in data for field in ('app', 'rank')):
            abort(400, message="Missing application or rank indices")
        stat = AnomalyStat(
            app=0, rank=0, key='0:0:0',
            count=0, eta=0, rho=0, tau=0, phi=0, min=0, max=0
        )
        stat.from_dict(data, partial_update=True)
        return stat

    @staticmethod
    def create_from(app, rank, stats: Statistics):
        """Create a new anomaly statistics"""
        (_count, _eta, _rho, _tau, _phi, _min, _max) = stats.get_state()
        stat = AnomalyStat(
            app=app, rank=rank, key='{}:{}:0'.format(app, rank),
            count=_count, eta=_eta, rho=_rho, tau=_tau, phi=_phi,
            min=_min, max=_max
        )
        return stat

    def from_dict(self, data, partial_update=True):
        """Import anomaly statistics from a dictionary"""
        for field in data.keys():
            try:
                setattr(self, field, data[field])
            except KeyError:
                if not partial_update:
                    abort(400)

        if 'key' not in data:
            setattr(self, 'key', '{}:{}:0'.format(
                data['app'], data['id']
            ))

    def to_dict(self):
        """Export anomaly statistics to a dictionary"""
        return {
            'id': self.id,
            'app': self.app,
            'rank': self.rank,
            'key': self.key,
            'count': self.count,
            'eta': self.eta,
            'rho': self.rho,
            'tau': self.tau,
            'phi': self.phi,
            'min': self.min,
            'max': self.max
        }

    def to_stats(self):
        """Export anomaly statistics to Statistics object"""
        stats = Statistics.fromstate(
            (self.count, self.eta, self.rho, self.tau, self.phi,
             self.min, self.max)
        )
        return stats


class AnomalyData(db.Model):
    """
    Anomaly data
    """
    __tablename__ = 'anomalydata'
    id = db.Column(db.Integer, primary_key=True)

    # step & the number of detected anomalies
    step = db.Column(db.Integer, index=True, default=0)
    n = db.Column(db.Integer, default=0)

    # key to statistics
    stat_id = db.Column(db.Integer, db.ForeignKey('anomalystat.id'))

    def __repr__(self):
        return '<AnomalyData {}:{}>'.format(self.step, self.n)

    @staticmethod
    def create(data, owner):
        """Create a new anomaly data"""
        d = AnomalyData(step=0, n=0, owner=owner)
        d.from_dict(data, partial_update=True)
        return d

    def from_dict(self, data, partial_update=True):
        """Import anomaly statistics from a dictionary"""
        for field in data.keys():
            try:
                setattr(self, field, data[field])
            except KeyError:
                if not partial_update:
                    abort(400)


class Execution(db.Model):
    """The Execution model"""
    __tablename__ = 'executions'
    id = db.Column(db.String(), primary_key=True)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    pid = db.Column(db.Integer, default=0)  # program id
    rid = db.Column(db.Integer, default=0)  # rank id
    tid = db.Column(db.Integer, default=0)  # thread id
    fid = db.Column(db.Integer, default=0)  # function id

    fname = db.Column(db.String(), default='Unknown')  # function name

    label = db.Column(db.Integer, default=0)      # 1 is anomaly; otherwise 0
    t_entry = db.Column(db.Integer, default=0)    # entry time
    t_exit = db.Column(db.Integer, default=0)     # exit time
    t_runtime = db.Column(db.Integer, default=0)  # run time (exit - entry)

    # parent = db.relationship()

    @staticmethod
    def create(data):
        """Create a new execution"""
        _exec = Execution()
        _exec.from_dict(data, partial_update=False)
        return _exec

    def from_dict(self, data: dict, partial_update=True):
        """Import execution data from a dictionary"""
        for field in data.keys():
            try:
                setattr(self, field, data[field])
            except KeyError:
                if not partial_update:
                    abort(400)

        if 't_runtime' not in data:
            try:
                setattr(self, 't_runtime', data['t_exit'] - data['t_entry'])
            except KeyError:
                abort(400)

    def to_dict(self):
        """Export execution data to a dictionary"""
        return {
            'id': self.id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'pid': self.pid,
            'rid': self.rid,
            'tid': self.tid,
            'fid': self.fid,
            'fname': self.fname,
            'label': self.label,
            't_entry': self.t_entry,
            't_exit': self.t_exit,
            't_runtime': self.t_runtime
        }
