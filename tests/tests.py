import unittest
import json

from server import create_app
from server.utils import MessageGenerator


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.ctx = self.app.app_context()
        self.ctx.push()

        self.client = self.app.test_client()

    def tearDown(self):
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

    def test_runstats(self):
        n_messages = 50
        msz_size = 1024 * 1024
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
