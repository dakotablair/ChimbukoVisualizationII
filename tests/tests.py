import unittest
import json

from server import create_app, db
# from server.models import Execution
from server.utils import MessageGenerator


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.ctx = self.app.app_context()
        self.ctx.push()

        db.drop_all()  # just in case
        db.create_all()

        self.client = self.app.test_client()

    def tearDown(self):
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
        # if body is not None and body != '':
        #     print(body)
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
        r, s, h = self.post('/api/anomalystats', {'id': 0, 'val1': 10, 'val2': 100})
        r, s, h = self.post('/api/anomalystats', {'id': 0, 'val1': 20, 'val2': 200})
        r, s, h = self.post('/api/anomalystats', {'id': 0, 'val1': 30, 'val2': 300})


    def test_runstats(self):
        n_messages = 50
        msz_size = 1024
        interval = -1

        gen = MessageGenerator(n_messages, msz_size, interval)

        # post message
        gen.start()
        for i in range(n_messages):
            r, s, h = self.post('/api/messages',
                                data={'rank': 0, 'data': gen.get()})
            self.assertEqual(s, 200)

        # get request_per_second
        r, s, h = self.get('/stats')
        self.assertEqual(s, 200)
        print("\n\tRequest/sec: {:.3f} ... ".format(
            r['requests_per_second']), end='')

        # get message (i.e. mean and std. dev.)
        r, s, h = self.get('/api/stat/0')
        self.assertEqual(s, 200)

        d_mean = abs(float(r['mean']) - gen.mean)
        d_stddev = abs(float(r['stddev']) - gen.std_dev)

        self.assertAlmostEqual(d_mean, 0.0, delta=1.0)
        self.assertAlmostEqual(d_stddev, 0.0, delta=1.0)
        self.assertEqual(n_messages, r['count'])

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
