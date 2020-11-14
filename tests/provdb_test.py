import sys
import json
import random
import time

import pymargo
from pymargo.core import Engine

from pysonata.provider import SonataProvider
from pysonata.client import SonataClient
from pysonata.admin import SonataAdmin

def test(engine, filename):
    address = str(engine.addr())
    admin = SonataAdmin(engine)
    client = SonataClient(engine)

    admin.attach_database(address, 0, 'provdb', 'unqlite', "{ \"path\" : \"%s\" }" % filename)
    database = client.open(address, 0, 'provdb')

    collection = database.open('anomalies')
    print("There are", collection.size, "records in total.")
    all_records = [ json.loads(x) for x in collection.all ]

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
         
    #index = 8
    #print("Let's see first 10 executions in iostep {}:".format(index))
    #print("event_id\tentry\truntime\tfid\tfunc")
    #ids = random.sample(range(0, len(iostep_dict[index])), 10)
    #for id in ids:
    #    exec = iostep_dict[index][id]
    #    print("{}\t{}\t{}\t{}\t{}".format( \
    #        exec['event_id'], \
    #        exec['entry'], exec['runtime_total'], \
    #        exec['fid'], exec['func'][:15]))

    #pid = rid = 0
    #jx9_filter = "function($record) { return $record.pid == %d &&" \
    #        "$record.rid == %d; }" % (pid, rid)
    #filtered_records = [ json.loads(x) for x in collection.filter(jx9_filter) ]
    #print("There are", len(filtered_records), "records that are GPU events.")
    #print("The first one is:")
    #print(filtered_records[0])

    admin.detach_database(address, 0, 'provdb')

if __name__ == '__main__':
    argc = len(sys.argv)
    if (argc < 2):
        filename = 'provdb.unqlite'
    else:
        filename = sys.argv[1]

    with Engine('na+sm', pymargo.server) as engine:
        provider = SonataProvider(engine, 0)
        test(engine, filename)
        del provider
        engine.finalize()
