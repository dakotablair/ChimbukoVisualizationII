import unittest
import json

from server import create_app, db


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()

        self.ctx = self.app.app_context()
        self.ctx.push()

        db.drop_all()  # just in case
        db.create_all()

        self.client = self.app.test_client()

    def tearDown(self):
        # If I drop DB before any asynchronous tasks are completed,
        # it will cause error. How to smoothly resolve this problem?
        # currently, I make sure each test containing celery task
        # to be completed before calling tearDown.
        # db.drop_all()
        self.ctx.pop()

    def get_headers(self):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        return headers

    def post(self, url, data=None):
        d = data if data is None else json.dumps(data)
        rv = self.client.post(url, data=d, headers=self.get_headers())

        body = rv.get_data(as_text=True)
        if body is not None and body != '':
            try:
                body = json.loads(body)
            except:  # noqa: E722
                pass
        return body, rv.status_code, rv.headers

    def get(self, url):
        rv = self.client.get(url, headers=self.get_headers())
        body = rv.get_data(as_text=True)
        if body is not None and body != '':
            try:
                body = json.loads(body)
            except:  # noqa: E722
                pass
        return body, rv.status_code, rv.headers

    def test_anomalystats(self):
        import random
        import time
        def get_random_stats():
            return {
                "count": random.randint(0,100),
                "accumulate": random.randint(0,100),
                "minimum": random.randint(0,100),
                "maximum": random.randint(0,100),
                "mean": random.randint(0,100),
                "stddev": random.randint(0,100),
                "skewness": random.randint(-100,100),
                "kurtosis": random.randint(-100,100)
            }

        def get_random_data(app, rank, step):
            return {
                "app": app,
                "rank": rank,
                "step": step,
                "min_timestamp": random.randint(0,100),
                "max_timestamp": random.randint(0, 100),
                "n_anomalies": random.randint(0, 100),
                "stat_id": '{}:{}'.format(app, rank)
            }

        def get_random_anomaly(app, rank, start_step, end_step):
            return {
                "key": '{}:{}'.format(app, rank),
                "stats": get_random_stats(),
                "data": [
                    get_random_data(app, rank, step)
                    for step in range(start_step, end_step, 1)
                ]
            }

        def get_random_func(n_func):
            data = [
                {
                    "fid": fid,
                    "name": 'func {}'.format(fid),
                    "stats": get_random_stats(),
                    "inclusive": get_random_stats(),
                    "exclusive": get_random_stats()
                } for fid in range(n_func)
            ]
            return data

        # post only anomaly statistics
        anomaly_payload = {
            'created_at': 123,
            'anomaly': [
                get_random_anomaly(0, 0, 0, 10),
                get_random_anomaly(0, 1, 0, 5),
                get_random_anomaly(0, 2, 0, 3)
            ]
        }
        r, s, h = self.post('/api/anomalydata', anomaly_payload)
        self.assertEqual(s, 202)
        time.sleep(0.1)

        # check anomaly statistics
        for d in anomaly_payload['anomaly']:
            app, rank = d['key'].split(':')
            r, s, h = self.get('/api/anomalystats?app={}&rank={}'.format(app, rank))
            self.assertEqual(s, 200)
            r = r[0]
            self.assertEqual(r['created_at'], 123)
            for k, v in d['stats'].items():
                self.assertEqual(v, r['stats'][k])

            r, s, h = self.get('/api/anomalydata?app={}&rank={}'.format(app, rank))
            self.assertEqual(s, 200)
            for dd in d['data']:
                step = dd['step']
                [self.assertEqual(v, r[step][k]) for k, v in dd.items() if k in r[step]]

        # post only func statistics
        func_payload = {
            'created_at': 123,
            'func': get_random_func(10)
        }
        r, s, h = self.post('/api/anomalydata', func_payload)
        self.assertEqual(s, 202)
        time.sleep(0.1)

        # check func statistics
        for fid in range(10):
            r, s, h = self.get('/api/funcstats?fid={}'.format(fid))
            self.assertEqual(s, 200)
            r = r[0]
            for k, v in func_payload['func'][fid].items():
                if isinstance(v, dict):
                    for k1, v1 in v.items():
                        self.assertEqual(r[k][k1], v1)
                else:
                    self.assertEqual(r[k], v)

        # post both
        payload = {
            'created_at': 124,
            'anomaly': [
                get_random_anomaly(0, 0, 10, 15),
                get_random_anomaly(0, 1, 5, 10),
                get_random_anomaly(0, 2, 3, 8)
            ],
            'func': get_random_func(10)
        }
        r, s, h = self.post('/api/anomalydata', payload)
        self.assertEqual(s, 202)
        time.sleep(0.1)

        # check anomaly statistics
        for d in payload['anomaly']:
            app, rank = d['key'].split(':')
            r, s, h = self.get('/api/anomalystats?app={}&rank={}'.format(app, rank))
            self.assertEqual(s, 200)
            r = r[0]
            self.assertEqual(r['created_at'], 124)
            for k, v in d['stats'].items():
                self.assertEqual(v, r['stats'][k])

            r, s, h = self.get('/api/anomalydata?app={}&rank={}&limit=5'.format(app, rank))
            self.assertEqual(s, 200)
            for i, dd in enumerate(d['data']):
                [self.assertEqual(v, r[i][k]) for k, v in dd.items() if k in r[i]]

        # check func statistics
        for fid in range(10):
            r, s, h = self.get('/api/funcstats?fid={}'.format(fid))
            self.assertEqual(s, 200)
            r = r[0]
            for k, v in payload['func'][fid].items():
                if isinstance(v, dict):
                    for k1, v1 in v.items():
                        self.assertEqual(r[k][k1], v1)
                else:
                    self.assertEqual(r[k], v)

    def test_execdata(self):
        import time
        r, s, h = self.get('/api/executions')
        self.assertEqual(s, 400)

        r, s, h = self.get('/api/executions?min_ts=0')
        self.assertEqual(s, 200)
        self.assertEqual(len(r), 0)

        # post execution only
        exec_payload = {
            'exec': [
                {
                    'key': 'exec 0',
                    'name': 'func 0',
                    'pid': 0,
                    'rid': 1,
                    'tid': 2,
                    'fid': 0,
                    'entry': 0,
                    'exit': 100,
                    'runtime': 100,
                    'exclusive': 30,
                    'label': 1,
                    'parent': 'root',
                    'n_children': 1,
                    'n_messages': 0
                },
                {
                    'key': 'exec 1',
                    'name': 'func 1',
                    'pid': 0,
                    'rid': 1,
                    'tid': 2,
                    'fid': 0,
                    'entry': 10,
                    'exit': 80,
                    'runtime': 70,
                    'exclusive': 50,
                    'label': 1,
                    'parent': 'exec 0',
                    'n_children': 1,
                    'n_messages': 2
                },
                {
                    'key': 'exec 2',
                    'name': 'func 2',
                    'pid': 0,
                    'rid': 1,
                    'tid': 2,
                    'fid': 0,
                    'entry': 30,
                    'exit':  50,
                    'runtime': 20,
                    'exclusive': 20,
                    'label': -1,
                    'parent': 'exec 1',
                    'n_children': 0,
                    'n_messages': 4
                }
            ]
        }
        r, s, h = self.post('/api/executions', exec_payload)
        self.assertEqual(s, 202)
        time.sleep(0.1)

        # check
        r, s, h = self.get('/api/executions?min_ts=10&max_ts=80')
        self.assertEqual(s, 200)
        self.assertEqual(len(r), 2)
        for i, ex in enumerate(exec_payload['exec'][1:]):
            for k, v in ex.items():
                self.assertEqual(r[i][k], v)

        # post communication only
        comm_payload = {
            'comm': [
                {
                    "execdata_key": "exec 1",
                    "type": "SEND",
                    "src": 0,
                    "tar": 1,
                    "size": 100,
                    "tag": 20,
                    "timestamp": 15
                },
                {
                    "execdata_key": "exec 1",
                    "type": "RECV",
                    "src": 1,
                    "tar": 0,
                    "size": 100,
                    "tag": 20,
                    "timestamp": 60
                },
                {
                    "execdata_key": "exec 2",
                    "type": "SEND",
                    "src": 2,
                    "tar": 3,
                    "size": 200,
                    "tag": 40,
                    "timestamp": 35
                },
                {
                    "execdata_key": "exec 2",
                    "type": "RECV",
                    "src": 3,
                    "tar": 2,
                    "size": 50,
                    "tag": 40,
                    "timestamp": 45
                }
            ]
        }
        r, s, h = self.post('/api/executions', comm_payload)
        self.assertEqual(s, 202)
        time.sleep(0.1)

        # check
        r, s, h = self.get('/api/executions?min_ts=10&max_ts=80&with_comm=1')
        self.assertEqual(s, 200)
        self.assertEqual(len(r), 2)
        check_comm = []
        for ex in r:
            check_comm += ex['comm']
        self.assertEqual(len(check_comm), 4)
        for i, comm in enumerate(comm_payload['comm']):
            for k, v, in comm.items():
                self.assertEqual(check_comm[i][k], v)

        # check
        exec_payload.update(comm_payload)
        r, s, h = self.get('/api/executions?min_ts=-1&with_comm=1')
        self.assertEqual(s, 200)
        self.assertEqual(len(r), 3)
        for i, ex in enumerate(exec_payload['exec']):
            for k, v in ex.items():
                if isinstance(v, dict):
                    self.assertEqual(k, 'comm')
                    for k2, v2 in v.items():
                        self.assertEqual(r[i][k][k2], v)
                else:
                    self.assertEqual(r[i][k], v)

