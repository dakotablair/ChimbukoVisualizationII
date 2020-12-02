import sys
import json
import random
import time
import glob

import pymargo
from pymargo.core import Engine

from pysonata.provider import SonataProvider
from pysonata.client import SonataClient
from pysonata.admin import SonataAdmin


def test(address, nshard):
    engine = Engine(address.split(':')[0], pymargo.client)
    client = SonataClient(engine)

    for i in range(nshard):
        pdb_name = 'provdb.' + str(i)
        pdb = client.open(address, 0, pdb_name)
        col = pdb.open('anomalies')
        print("Shard {} has the size of {}.".format(i, col.size))


if __name__ == '__main__':
    argc = len(sys.argv)
    if (argc < 2):
        raise "Enter the path!"

    path = sys.argv[1]
    with Engine('ofi+tcp;ofi_rxm', pymargo.server) as engine:
        provider = SonataProvider(engine, 0)
        addr = str(engine.addr())
        print(addr)
        admin = SonataAdmin(engine)
        unqlite_files = glob.glob(path + '/*.unqlite')
        # extract number as index
        ids = [int(f.split('.')[-2]) for f in unqlite_files]
        # sort as numeric values
        inds = sorted(range(len(ids)), key=lambda k: ids[k])
        files = [unqlite_files[i] for i in inds]  # files in correct order
        for i, f in enumerate(files):
            pdb_name = 'provdb.' + str(i)
            admin.attach_database(address, 0, pdb_name, 'unqlite',
                                  "{ \"path\" : \"%s\" }" % f)

        test(addr, len(files))

        del provider
        engine.finalize()
