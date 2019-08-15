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
        import os
        import numpy as np
        import time
        from runstats import Statistics
        from collections import defaultdict

        my_runstats = defaultdict(lambda: Statistics())
        my_n_anomalies = defaultdict(int)
        worker_id = []

        MAX_N_UPDATES = 50
        MIN_N_UPDATES = 20
        N_APPS = 3
        N_RANKS = 10
        INTERVAL = 1000  # millisecond

        # to make this test is more realistic,
        # there could be different number of updates per (app and rank)
        n_updates = {}
        for app_id in range(N_APPS):
            for rank_id in range(N_RANKS):
                n_updates['{}:{}'.format(app_id, rank_id)] = \
                    np.random.randint(MIN_N_UPDATES, MAX_N_UPDATES+1)

        # post Anomaly stats from parameter server
        for i in range(MAX_N_UPDATES):
            payload = []
            for app_id in range(N_APPS):
                for rank_id in range(N_RANKS):
                    key = '{}:{}'.format(app_id, rank_id)
                    if n_updates[key] <= i:
                        continue

                    n_anomaly = np.random.randint(1, 100)

                    _runstat = my_runstats[key]
                    my_n_anomalies[key] = my_n_anomalies[key] + n_anomaly

                    _runstat.push(n_anomaly)

                    try:
                        stddev = _runstat.stddev()
                        skewness = _runstat.skewness()
                        kurtosis = _runstat.kurtosis()
                    except ZeroDivisionError:
                        stddev = 0
                        skewness = 0
                        kurtosis = 0

                    _payload = {
                        'app': int(app_id),
                        'rank': int(rank_id),
                        'stats': {
                            'n_updates': int(len(_runstat)),
                            'n_anomalies': my_n_anomalies[key],
                            'n_min_anomalies': _runstat.minimum(),
                            'n_max_anomalies': _runstat.maximum(),
                            'mean': _runstat.mean(),
                            'stddev': stddev,
                            'skewness': skewness,
                            'kurtosis': kurtosis
                        },
                        'data': [{
                            'n_anomaly': n_anomaly,
                            'step': i,
                            'min_timestamp': float(i * INTERVAL),
                            'max_timestamp': float((i + 1) * INTERVAL),
                            'stat_id': key
                        }]
                    }
                    payload.append(_payload)

            # if 'delete_old' calls too frequently, it becomes error-prone! why??
            r, s, h = self.post('/api/anomalydata',
                                {
                                    'payload': payload,
                                    'delete_old': ((i+1) % 10 == 0) or (i+1 == MAX_N_UPDATES)
                                })
            self.assertEqual(s, 202)
            worker_id.append(os.path.basename(h['Location']))
            # Note that it does not gaurantee that post operations are
            # executed in order because celery workers may not be launched
            # in the same order. To guarantee the order, uncomment the
            # below line.
            time.sleep(0.05)

        # wait untill all tasks are completed
        n_tries = 0
        while len(worker_id) and n_tries < 100:
            to_remove = []
            for wid in worker_id:
                r, s, h = self.get('/tasks/status/' + worker_id[0])
                if s == 201:
                    to_remove.append(wid)

            worker_id = [wid for wid in worker_id if wid not in to_remove]
            n_tries = n_tries + 1
            time.sleep(0.1)
        self.assertEqual(len(worker_id), 0)

        # for the test purpose,
        # wait until all data is written into the database
        # time.sleep(1)

        r, s, h = self.get('/api/anomalystats')
        self.assertEqual(s, 200)
        self.assertEqual(len(r), N_APPS * N_RANKS)

        # check statistics
        for key, _rs in my_runstats.items():
            app_id, rank_id = key.split(':')
            r, s, h = self.get('/api/anomalydata?app={:d}&rank={:d}'.format(
                int(app_id), int(rank_id)
            ))

            _stat = r['stat']
            _data = r['data']

            self.assertEqual(_stat['n_updates'], n_updates[key])
            self.assertEqual(_stat['n_anomalies'], my_n_anomalies[key])
            self.assertEqual(_stat['n_min_anomalies'], _rs.minimum())
            self.assertEqual(_stat['n_max_anomalies'], _rs.maximum())
            self.assertAlmostEqual(_stat['mean'], _rs.mean(), delta=0.001)
            self.assertAlmostEqual(_stat['stddev'], _rs.stddev(), delta=0.001)
            self.assertAlmostEqual(_stat['skewness'], _rs.skewness(), delta=0.001)
            self.assertAlmostEqual(_stat['kurtosis'], _rs.kurtosis(), delta=0.001)
            self.assertEqual(len(_data), n_updates[key])

    # def test_executions(self):
    #     # try to get an execution in the empty database
    #     r, s, h = self.get('/api/execution/id_0')
    #     self.assertEqual(s, 400)
    #
    #     r, s, h = self.get('/api/executions')
    #     self.assertEqual(s, 200)
    #     self.assertEqual(len(r), 0)
    #
    #     # post a single execution
    #     r, s, h = self.post('/api/execution', data={
    #         'id': 'id_0', 'pid': 0, 'rid': 0, 'tid': 0, 'fid': 0,
    #         'fname': 'func_0', 'label': 0, 't_entry': 10, 't_exit': 60,
    #     })
    #     self.assertEqual(s, 200)
    #
    #     # get the execution
    #     r, s, h = self.get('/api/execution/id_0')
    #     self.assertEqual(s, 200)
    #     self.assertEqual('id_0', r['id'])
    #     self.assertEqual('func_0', r['fname'])
    #     self.assertEqual(10, r['t_entry'])
    #     self.assertEqual(60, r['t_exit'])
    #
    #     # post a list of executions
    #     r, s, h = self.post('/api/executions', data=[
    #         {
    #             'id': 'id_1', 'pid': 0, 'rid': 0, 'tid': 0, 'fid': 1,
    #             'fname': 'func_1', 'label': 0, 't_entry': 15, 't_exit': 20,
    #         },
    #         {
    #             'id': 'id_2', 'pid': 0, 'rid': 0, 'tid': 0, 'fid': 2,
    #             'fname': 'func_2', 'label': 1, 't_entry': 30, 't_exit': 50,
    #         },
    #         {
    #             'id': 'id_3', 'pid': 0, 'rid': 0, 'tid': 0, 'fid': 1,
    #             'fname': 'func_1', 'label': 0, 't_entry': 35, 't_exit': 40,
    #         }
    #     ])
    #     self.assertEqual(s, 200)
    #
    #     # get executions (default)
    #     r, s, h = self.get('/api/executions')
    #     self.assertEqual(s, 200)
    #     self.assertEqual(len(r), 4)
    #     self.assertEqual(r[0]['t_entry'], 10)
    #     self.assertEqual(r[1]['t_entry'], 15)
    #     self.assertEqual(r[2]['t_entry'], 30)
    #     self.assertEqual(r[3]['t_entry'], 35)
    #
    #     # get execution (use t_exit and desc order)
    #     r, s, h = self.get('/api/executions?time=t_exit&order=desc')
    #     self.assertEqual(s, 200)
    #     self.assertEqual(len(r), 4)
    #     self.assertEqual(r[0]['t_exit'], 60)
    #     self.assertEqual(r[1]['t_exit'], 50)
    #     self.assertEqual(r[2]['t_exit'], 40)
    #     self.assertEqual(r[3]['t_exit'], 20)
    #
    #     # get execution (use t_entry && desc order && label=1)
    #     r, s, h = self.get('/api/executions?time=t_entry&order=desc&label=1')
    #     self.assertEqual(s, 200)
    #     self.assertEqual(len(r), 1)
    #     self.assertEqual(r[0]['fname'], 'func_2')
    #
    #     # get execution (use t_entry && desc order && label=0 && since=20)
    #     r, s, h = self.get(
    #         '/api/executions?time=t_entry&order=desc&label=0&since=20')
    #     self.assertEqual(s, 200)
    #     self.assertEqual(len(r), 1)
    #     self.assertEqual(r[0]['id'], 'id_3')
    #
    #     # get execution (use t_entry && desc order && since=20 && until=100)
    #     r, s, h = self.get(
    #         '/api/executions?time=t_entry&order=desc&since=20&until=100')
    #     self.assertEqual(s, 200)
    #     self.assertEqual(len(r), 2)
    #     self.assertEqual(r[0]['id'], 'id_3')
    #     self.assertEqual(r[1]['id'], 'id_2')
