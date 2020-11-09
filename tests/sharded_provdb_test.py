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

def test(engine, path):
    address = str(engine.addr())
    admin = SonataAdmin(engine)
    client = SonataClient(engine)

    unqlite_files = glob.glob(path + '/*.unqlite')
    # extract number as index
    ids = [int(f.split('.')[-2]) for f in unqlite_files]
    # sort as numeric values
    inds = sorted(range(len(ids)), key=lambda k: ids[k])
    files = [unqlite_files[i] for i in inds]  # files in correct order

    pdb_collections = []
    pdb_names = []
    for i, f in enumerate(files):
        pdb_name = 'provdb.' + str(i)
        pdb_names.append(pdb_name)
        pdb_admin.attach_database(address, 0, pdb_name, 'unqlite',
                                  "{ \"path\" : \"%s\" }" % f)
        pdb = pdb_client.open(address, 0, pdb_name)
        pdb_collections.append(pdb.open('anomalies'))

    all_records = []
    for col in pdb_collections:
        record = [json.loads(x) for x in col.all]
        all_records += record
        print(col.size)
    
    iostep_dict = {}
    pids = []
    rids = []
    iosteps = []
    for record in all_records:
        pid, rid, io_step = record['pid'], record['rid'], record['io_step']
        id = (pid, rid, io_step)
        pids.append(pid)
        rids.append(rid)
        iosteps.append(io_step)
        if id not in iostep_dict:
            iostep_dict[id] = [record]
        else:
            iostep_dict[id].append(record)
    pids, rids, iosteps = list(set(pids)), list(set(rids)), list(set(iosteps))
    print("There are {} categories in total:".format(len(iostep_dict)))
    stat = [(x, len(iostep_dict[x])) for x in iostep_dict]
    stat.sort(key=lambda d: d[0])
    print(*stat, sep='\n')

    #pids, rids, iosteps = [0], [0,1], [0,1,2,3,4,5,6,7,8]
    for pid in pids:
        for rid in rids:
            for iostep in iosteps:
                t0 = time.clock()
                jx9_filter = "function($record) { return $record.pid == %d &&" \
                        "$record.rid == %d && $record.io_step == %d; }" % (pid, rid, iostep)
                filtered_records = [ json.loads(x) for x in collection.filter(jx9_filter) ]
                t1 = time.clock() - t0
                print("{}, {}, {}: {:.2f} seconds with {}\texecutions of memory" \
                        "size {:.2f}KB".format(pid, rid, iostep, t1, len(filtered_records), \
                        sys.getsizeof(filtered_records)*1./1024))

    for i, f in enumerate(files):
        admin.detach_database(address, 0, pdb_names[i])

if __name__ == '__main__':
    argc = len(sys.argv)
    if (argc < 2):
        raise "Enter the path!"

    path = sys.argv[1]
    with Engine('na+sm', pymargo.server) as engine:
        provider = SonataProvider(engine, 0)
        test(engine, path)
        del provider
        engine.finalize()
