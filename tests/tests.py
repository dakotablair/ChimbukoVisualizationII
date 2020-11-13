import unittest
import json

from server import create_app, db
from flask import _app_ctx_stack, current_app

# from server.provdb import ProvDB


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
        db.drop_all()
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
                "count": random.randint(0, 100),
                "accumulate": random.randint(0, 100),
                "minimum": random.randint(0, 100),
                "maximum": random.randint(0, 100),
                "mean": random.randint(0, 100),
                "stddev": random.randint(0, 100),
                "skewness": random.randint(-100, 100),
                "kurtosis": random.randint(-100, 100)
            }

        def get_random_data(app, rank, step):
            return {
                "app": app,
                "rank": rank,
                "step": step,
                "min_timestamp": random.randint(0, 100),
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

        def get_random_counter(app, n_counter):
            data = []
            for i in range(n_counter):
                data.append({
                    'app': app,
                    'counter': 'cpu {} %'.format(i),
                    'stats': {
                        "count": random.randint(0, 100),
                        "accumulate": random.randint(0, 100),
                        "minimum": random.randint(0, 100),
                        "maximum": random.randint(0, 100),
                        "mean": random.randint(0, 100),
                        "stddev": random.randint(0, 100),
                        "skewness": random.randint(-100, 100),
                        "kurtosis": random.randint(-100, 100)
                    }
                })
            return data

        # post only anomaly statistics
        anomaly_stats = {
            'created_at': 123,
            'anomaly': [
                get_random_anomaly(0, 0, 0, 10),
                get_random_anomaly(0, 1, 0, 5),
                get_random_anomaly(0, 2, 0, 3)
            ]
        }

        counter_stats = get_random_counter(0, 15)

        anomaly_payload = {
            'anomaly_stats': anomaly_stats,
            'counter_stats': counter_stats
        }

        r, s, h = self.post('/api/anomalydata', anomaly_payload)
        self.assertEqual(s, 202)
        time.sleep(1)  # wait until celery worker is done

        # check anomaly statistics
        for d in anomaly_payload['anomaly_stats']['anomaly']:
            app, rank = d['key'].split(':')
            r, s, h = self.get('/api/get_anomalystats?app={}&rank={}'.format(app, rank))
            self.assertEqual(s, 200)
            r = r[0]
            self.assertEqual(r['created_at'], 123)
            for k, v in d['stats'].items():
                self.assertEqual(v, r[k])

            r, s, h = self.get('/api/get_anomalydata?app={}&rank={}'.format(app, rank))
            self.assertEqual(s, 200)
            for dd in d['data']:
                step = dd['step']
                [self.assertEqual(v, r[step][k]) for k, v in dd.items() if k in r[step]]

        # post only func statistics
        func_payload = {
            'anomaly_stats': {
                'created_at': 123,
                'func': get_random_func(10)
            }
        }
        r, s, h = self.post('/api/anomalydata', func_payload)
        self.assertEqual(s, 202)
        time.sleep(0.1)

        # check func statistics
        for fid in range(10):
            r, s, h = self.get('/api/get_funcstats?fid={}'.format(fid))
            self.assertEqual(s, 200)
            r = r[0]
            for k, v in func_payload['anomaly_stats']['func'][fid].items():
                if isinstance(v, dict):
                    for k1, v1 in v.items():
                        self.assertEqual(r[k][k1], v1)
                else:
                    self.assertEqual(r[k], v)

        # post both
        payload = {
            'anomaly_stats': {
                'created_at': 124,
                'anomaly': [
                    get_random_anomaly(0, 0, 10, 15),
                    get_random_anomaly(0, 1, 5, 10),
                    get_random_anomaly(0, 2, 3, 8)
                ],
                'func': get_random_func(10)
            },
            'counter_stats': get_random_counter(0, 15)
        }

        print("......", self.app)
        r, s, h = self.post('/api/anomalydata', payload)
        self.assertEqual(s, 202)
        time.sleep(5)

        payload = payload['anomaly_stats']
        # check anomaly statistics
        for d in payload['anomaly']:
            app, rank = d['key'].split(':')
            r, s, h = self.get('/api/get_anomalystats?app={}&rank={}'.format(app, rank))
            self.assertEqual(s, 200)
            r = r[0]
            print(r)
            self.assertEqual(r['created_at'], 124)
            for k, v in d['stats'].items():
                self.assertEqual(v, r[k])

            r, s, h = self.get('/api/get_anomalydata?app={}&rank={}'.format(app, rank))
            self.assertEqual(s, 200)
            for i, dd in enumerate(d['data']):
                [self.assertEqual(v, r[i][k]) for k, v in dd.items() if k in r[i]]

        # check func statistics
        for fid in range(10):
            r, s, h = self.get('/api/get_funcstats?fid={}'.format(fid))
            self.assertEqual(s, 200)
            r = r[0]
            for k, v in payload['func'][fid].items():
                if isinstance(v, dict):
                    for k1, v1 in v.items():
                        self.assertEqual(r[k][k1], v1)
                else:
                    self.assertEqual(r[k], v)

    # def test_provdb(self):
    #     filtered_records = []
    #     jx9_filter = "function($record) { return " \
    #         "$record.pid == %d && " \
    #         "$record.rid == %d && " \
    #         "$record.io_step == %d; } " % (0, 1, 5)

    #     provdb = ProvDB(pdb_path='data/sample/provdb/',
    #                     pdb_sharded_num=1)
    #     collections = provdb.pdb_collections
    #     for col in collections:
    #         result = [json.loads(x) for x in col.filter(jx9_filter)]
    #         filtered_records += result
    #     self.assertEqual(len(filtered_records), 124)
