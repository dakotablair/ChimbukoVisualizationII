from flask import abort
from . import db
from .utils import timestamp


class AnomalyStat(db.Model):
    """Anomaly statistics"""
    __tablename__ = 'anomalystats'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)

    val1 = db.Column(db.Integer, default=0)
    val2 = db.Column(db.Integer, default=0)
    sum  = db.Column(db.Float, default=0)

    @staticmethod
    def create(data):
        """Create a new execution"""
        st = AnomalyStat()
        st.from_dict(data, partial_update=False)
        return st

    def from_dict(self, data, partial_update=True):
        """Import execution data from a dictionary"""
        for field in data.keys():
            try:
                setattr(self, field, data[field])
            except KeyError:
                if not partial_update:
                    abort(400)

    def to_dict(self):
        pass

    @staticmethod
    def on_updated(mapper, connection, target):
        tb = AnomalyStat.__table__
        sum = target.val1 + target.val2 + target.sum
        connection.execute(
            tb.update().where(tb.c.id==target.id).values(sum=sum)
        )

db.event.listen(AnomalyStat, 'after_update', AnomalyStat.on_updated)
db.event.listen(AnomalyStat, 'after_insert', AnomalyStat.on_updated)


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

# db.event.listen(Execution.source, 'set', Execution.on_changed_source)
