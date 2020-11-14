"""
Test script for "in-situ" mode
: send pseudo-anomaly statistics from parameter server

pseudo_ad.py :
- MPI program, each MPI processor represents (pseudo) AD module.
- It generates periodically (# anomalies) following
  given [mean, stdandard deviation] and send to parameter server.
- And, the (# anomalies)

"""
import requests
import time
import random
from collections import defaultdict
from runstats import Statistics


def timestamp():
    return int(round(time.time() * 1000))


def generate_random_data(n_ranks, step, dist):
    dataset = []
    ts = timestamp()
    for rank in range(n_ranks):
        mean, stddev = dist[rank]
        dataset.append({
            'n_anomaly': abs(random.normalvariate(mean, stddev)),
            'step': step,
            'min_timestamp': ts + random.randint(0, 1000),
            'max_timestamp': ts + 1000 + random.randint(500, 1000),
            'stat_id': '0:{:d}'.format(rank)
        })
    return dataset


def generate_random_normal(n_ranks):
    dist = {}
    for rank in range(n_ranks):
        mean = float(random.randint(0, 50))
        stddev = float(random.randint(1, 10))
        dist[rank] = [mean, stddev]
    return dist


if __name__ == '__main__':
    import sys

    n_ranks = 1000  # total number of MPI processors
    max_steps = 10000  # large number for long test
    interval = 1  # sec
    url = 'http://127.0.0.1:5002/api/anomalydata'  # vis server

    if len(sys.argv) > 1:
        n_ranks = int(sys.argv[1])
        max_steps = int(sys.argv[2])
        interval = int(sys.argv[3])
        url = sys.argv[4]

    print("# Ranks: ", n_ranks)
    print("# Steps: ", max_steps)
    print("Interval: ", interval)
    print("URL: ", url)

    stats = defaultdict(lambda: Statistics())
    acc_n_anomalies = defaultdict(int)

    # init. (set random normal distribution for each rank)
    dist = generate_random_normal(n_ranks)

    # start ...
    for step in range(max_steps):
        dataset = generate_random_data(n_ranks, step, dist)

        # update runstats & make payload
        anomaly = []
        for rank, data in enumerate(dataset):
            n_anomaly = data['n_anomaly']
            stats[rank].push(n_anomaly)
            acc_n_anomalies[rank] += n_anomaly

            stddev = 0
            skewness = 0
            kurtosis = 0
            try:
                stddev = stats[rank].stddev()
                skewness = stats[rank].skewness()
                kurtosis = stats[rank].kurtosis()
            except ZeroDivisionError:
                pass

            anomaly.append({
                'app': 0,
                'rank': rank,
                'stats': {
                    'n_updates': step + 1,
                    'n_anomalies': acc_n_anomalies[rank],
                    'n_min_anomalies': stats[rank].minimum(),
                    'n_max_anomalies': stats[rank].maximum(),
                    'mean': stats[rank].mean(),
                    'stddev': stddev,
                    'skewness': skewness,
                    'kurtosis': kurtosis
                },
                'data': [data]
            })

        payload = {
            'anomaly_stats': {
                'created_at': timestamp(),
                'anomaly': anomaly
            },
            'counter_stats': []
        }
        # post request
        requests.post(url=url, json=payload)

        # interval
        time.sleep(interval)

        if step % 10 == 0:
            print('Sent {:d}-th step.'.format(step + 1))
            dist = generate_random_normal(n_ranks)
