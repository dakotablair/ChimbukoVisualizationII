import unittest
import json

from server.server import app
from server.utils import MessageGenerator

app.config['TESTING'] = True


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def tearDown(self):
        pass

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
        n_messages = 10
        msz_size = 4 * 1000
        interval = -1

        gen = MessageGenerator(n_messages, msz_size, interval)

        # post message
        gen.start()
        for i in range(n_messages):
            r, s, h = self.post('/api/messages',
                                data={'rank': 0, 'data': gen.get()})
            self.assertEqual(s, 200)

        # get message (i.e. mean and std. dev.)
        r, s, h = self.get('/api/stat/0')
        self.assertEqual(s, 200)

        d_mean = abs(float(r['mean']) - gen.mean)
        d_stddev = abs(float(r['stddev']) - gen.std_dev)

        self.assertAlmostEqual(d_mean, 0.0, delta=1.0)
        self.assertAlmostEqual(d_stddev, 0.0, delta=1.0)
