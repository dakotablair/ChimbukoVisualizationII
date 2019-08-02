import unittest
import json
import os
import time

# import mock

from server import create_app, db


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.ctx = self.app.app_context()
        self.ctx.push()

        # db.drop_all()  # just in case
        # db.create_all()

        self.client = self.app.test_client()

    def tearDown(self):
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
        import numpy as np
        # N = 100
        N = 100000
        data = [
            {
                'app_rank': '{}:{}'.format(np.random.randint(0, 3), np.random.randint(0, 10)),
                'step': np.random.randint(0, 100),
                'n': np.random.randint(1, 100)
            } for _ in range(N)
        ]
        # print(data)

        # app_rank = set([d['app_rank'] for d in data])
        # print(list(app_rank))

        r, s, h = self.post('/api/anomalydata', data)
        print(r, s, h)

        # worker_id = []
        # r, s, h = self.post(
        #     '/api/anomalystats',
        #     {'app': 0, 'rank': 0, 'step': 0, 'n': 10}
        # )
        # print(r, s, h)


        # self.assertEqual(s, 202)
        # worker_id.append(os.path.basename(h['Location']))
        #
        # r, s, h = self.post(
        #     '/api/anomalystats',
        #     [
        #         {'id': 0, 'step': 1, 'mean': 10.3, 'stddev': 4.2},
        #         {'id': 1, 'step': 0, 'mean': 1.0, 'stddev': 0.3},
        #     ]
        # )
        # self.assertEqual(s, 202)
        # worker_id.append(os.path.basename(h['Location']))
        #
        # n_tries = 0
        # while len(worker_id) and n_tries < 100:
        #     to_remove = []
        #     for wid in worker_id:
        #         r, s, h = self.get('/tasks/status/' + worker_id[0])
        #         if s == 201:
        #             to_remove.append(wid)
        #
        #     worker_id = [wid for wid in worker_id if wid not in to_remove]
        #     n_tries = n_tries + 1
        #     time.sleep(0.1)
        # self.assertEqual(len(worker_id), 0)
        #
        # time.sleep(1)
        # print("")
        # r, s, h = self.get('/api/anomalystats')
        # print(r, s, h)


    def test_executions(self):
        # try to get an execution in the empty database
        r, s, h = self.get('/api/execution/id_0')
        self.assertEqual(s, 400)

        r, s, h = self.get('/api/executions')
        self.assertEqual(s, 200)
        self.assertEqual(len(r), 0)

        # post a single execution
        r, s, h = self.post('/api/execution', data={
            'id': 'id_0', 'pid': 0, 'rid': 0, 'tid': 0, 'fid': 0,
            'fname': 'func_0', 'label': 0, 't_entry': 10, 't_exit': 60,
        })
        self.assertEqual(s, 200)

        # get the execution
        r, s, h = self.get('/api/execution/id_0')
        self.assertEqual(s, 200)
        self.assertEqual('id_0', r['id'])
        self.assertEqual('func_0', r['fname'])
        self.assertEqual(10, r['t_entry'])
        self.assertEqual(60, r['t_exit'])

        # post a list of executions
        r, s, h = self.post('/api/executions', data=[
            {
                'id': 'id_1', 'pid': 0, 'rid': 0, 'tid': 0, 'fid': 1,
                'fname': 'func_1', 'label': 0, 't_entry': 15, 't_exit': 20,
            },
            {
                'id': 'id_2', 'pid': 0, 'rid': 0, 'tid': 0, 'fid': 2,
                'fname': 'func_2', 'label': 1, 't_entry': 30, 't_exit': 50,
            },
            {
                'id': 'id_3', 'pid': 0, 'rid': 0, 'tid': 0, 'fid': 1,
                'fname': 'func_1', 'label': 0, 't_entry': 35, 't_exit': 40,
            }
        ])
        self.assertEqual(s, 200)

        # get executions (default)
        r, s, h = self.get('/api/executions')
        self.assertEqual(s, 200)
        self.assertEqual(len(r), 4)
        self.assertEqual(r[0]['t_entry'], 10)
        self.assertEqual(r[1]['t_entry'], 15)
        self.assertEqual(r[2]['t_entry'], 30)
        self.assertEqual(r[3]['t_entry'], 35)

        # get execution (use t_exit and desc order)
        r, s, h = self.get('/api/executions?time=t_exit&order=desc')
        self.assertEqual(s, 200)
        self.assertEqual(len(r), 4)
        self.assertEqual(r[0]['t_exit'], 60)
        self.assertEqual(r[1]['t_exit'], 50)
        self.assertEqual(r[2]['t_exit'], 40)
        self.assertEqual(r[3]['t_exit'], 20)

        # get execution (use t_entry && desc order && label=1)
        r, s, h = self.get('/api/executions?time=t_entry&order=desc&label=1')
        self.assertEqual(s, 200)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]['fname'], 'func_2')

        # get execution (use t_entry && desc order && label=0 && since=20)
        r, s, h = self.get(
            '/api/executions?time=t_entry&order=desc&label=0&since=20')
        self.assertEqual(s, 200)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]['id'], 'id_3')

        # get execution (use t_entry && desc order && since=20 && until=100)
        r, s, h = self.get(
            '/api/executions?time=t_entry&order=desc&since=20&until=100')
        self.assertEqual(s, 200)
        self.assertEqual(len(r), 2)
        self.assertEqual(r[0]['id'], 'id_3')
        self.assertEqual(r[1]['id'], 'id_2')



# class MessageGenerator(object):
#     def __init__(self, n=100, size=1024 * 1024, interval=1000):
#         self.n = n                # total number of messages
#         self.size = size          # message size in bytes
#         self.interval = interval  # interval between messages in millisecond
#
#         self.mean = float(np.random.randint(0, 100))
#         self.std_dev = float(np.random.randint(10, 50))
#         self.count = int(self.size / 4)  # number of elements in a message
#
#         # thread
#         self.q = Queue()  # message queue
#         self.ev = threading.Event()  # terminating event
#         self.thread = threading.Thread(target=self._run)
#
#     def _run(self):
#         count = 0
#         while count < self.n:
#             # generate random data (normal distribution)
#             t_begin = time.time()
#             rd = np.random.normal(
#                 self.mean, self.std_dev, self.count).astype(np.float32)
#             rd = rd.tolist()
#             t_end = time.time()
#
#             # make interval
#             t_elapsed = t_end - t_begin
#             if t_elapsed < self.interval / 1000:
#                 time.sleep(self.interval / 1000 - t_elapsed)
#
#             # add to queue
#             self.q.put(rd)
#             count = count + 1
#
#     def start(self):
#         self.thread.start()
#
#     def get(self):
#         rd = self.q.get()
#         self.q.task_done()
#         return rd
