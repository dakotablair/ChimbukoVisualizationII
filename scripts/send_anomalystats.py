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
import numpy as np
import time
from mpi4py import MPI

MIN_MEAN_VAL = 0
MAX_MEAN_VAL = 100

def get_random_data(app, rank, step, n):
    return {
        'app_rank': '{}:{}'.format(app, rank),
        'step': step,
        'n': n
    }

def from_parameter_server(url, n_steps, interval, n_ranks, app=0):
    means = np.random.randint(MIN_MEAN_VAL, MAX_MEAN_VAL, n_ranks).tolist()
    stddevs = [np.sqrt(np.random.random() * mean) for mean in means]

    for step in range(n_steps):
        t0 = time.time()
        data = [
            get_random_data(
                app, rank, step,
                int(np.random.normal(mean, stddev)))
            for rank, mean, stddev in zip(range(n_ranks), means, stddevs)
        ]
        t1 = time.time()
        elapsed = t1 - t0
        if elapsed < interval:
            time.sleep(interval - elapsed)

        requests.post(url=url, json=data)

    return means, stddevs



def from_ad_module(url, n_steps, interval, rank, app=0):
    mean = np.random.randint(MIN_MEAN_VAL, MAX_MEAN_VAL)
    stddev = np.sqrt(np.random.random() * mean)

    for step in range(n_steps):
        t0 = time.time()
        data = get_random_data(
            app, rank, step, np.random.normal(mean, stddev))
        t1 = time.time()
        elapsed = t1 - t0
        if elapsed < interval:
            time.sleep(interval - elapsed)

        requests.post(url=url, json=data)

    return mean, stddev


if __name__ == '__main__':
    import sys

    # the number of steps
    n_steps = 20
    # time interval between post requests (sec)
    interval = 1
    # the number of ranks (only for from_parameter_server)
    n_ranks = 1000
    # url
    url='http://127.0.0.1:5000'

    # todo: parsing input arguments

    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()

    # post requests
    if size == 1:
        mean, stddev = from_parameter_server(
            url + '/api/anomalydata', n_steps, interval, n_ranks)
    else:
        mean, stddev = from_ad_module(
            url + '/api/anomalydata', n_steps, interval, rank)

    if not isinstance(mean, list):
        mean = [mean]

    if not isinstance(stddev, list):
        stddev = [stddev]

    # check correctness
    comm.Barrier()

    # For the test purpose, I need to make sure that
    # all celery workers finished jobs.
    if rank == 0:
        n_tries = 0
        active = 0
        scheduled = 0
        while n_tries < 100:
            resp = requests.get(url + '/tasks/inspect')
            data = resp.json()
            active = sum([len(v) for _, v in data['active'].items()])
            scheduled = sum([len(v) for _, v in data['scheduled'].items()])

            if active == 0 and scheduled == 0:
                break

            n_tries = n_tries + 1
            print('{}: active({}), scheduled({})'.format(
                n_tries, active, scheduled
            ))

    comm.Barrier()

    # just to make sure, all data is written to the database
    time.sleep(1)

    if size == 1:
        resp = requests.get(url + '/api/anomalystats')
    else:
        resp = requests.get(
            url + '/api/anomalystats?app=0&rank={}'.format(rank))

    retrived = resp.json()
    print('# Anomaly statistics: ', len(retrived))
    for r in retrived:
        r_rank = int(r['rank'])
        r_mean = r['mean']
        r_stddev = r['stddev']
        r_count = r['count']

        d_mean = abs(r_mean - mean[r_rank])
        d_stddev = abs(r_stddev - stddev[r_rank])
        d_count = abs(r_count - n_steps)

        if d_mean >= 1.0 or d_stddev >= 1.0 or d_count >= 1.0:
            print('')
            print('Rank: {}'.format(r_rank))
            print('Count: {:d} vs {:d}'.format(r_count, n_steps))
            print('Mean: {:.3f} vs {:.3f}'.format(r_mean, mean[r_rank]))
            print('Std: {:.3f} vs {:.3f}'.format(r_stddev, stddev[r_rank]))

    print('Done!')


