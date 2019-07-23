import requests

from server.utils import MessageGenerator

if __name__ == '__main__':
    import sys
    from mpi4py import MPI

    url = 'http://127.0.0.1:5000/api/messages'
    n_messages = 10
    msz_size = 40
    interval = 1000 # millisecond

    if len(sys.argv) > 1:
        url = sys.argv[1]
        n_messages = int(sys.argv[2])
        msz_size = int(sys.argv[3])
        interval = int(sys.argv[4])

    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()
    gen  = MessageGenerator(n_messages, msz_size, interval)

    # send messages
    print('Rank {} - Mean: {}, Std: {}'.format(rank, gen.mean, gen.std_dev))
    gen.start()
    for i in range(n_messages):
        rd = gen.get()
        msg = {
            'rank': rank,
            'data': rd
        }
        resp = requests.post(
            url=url,
            json=msg,
            headers={'Content-Type': 'application/json'}
        )

