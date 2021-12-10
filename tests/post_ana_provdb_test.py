import sys
import json
import random
import time

import pymargo
from pymargo.core import Engine

from pysonata.provider import SonataProvider
from pysonata.client import SonataClient
from pysonata.admin import SonataAdmin

import pandas as pd

def test(engine, filename):
    address = str(engine.addr())
    admin = SonataAdmin(engine)
    client = SonataClient(engine)

    admin.attach_database(address, 0, 'provdb', 'unqlite', "{ \"path\" : \"%s\" }" % filename)
    database = client.open(address, 0, 'provdb')

    collection = database.open('anomalies')
    print("There are", collection.size, "records in total.")

    columns = ["fid", "event_id", "func", "entry", "exit", "pid", "rid", "tid",
            "io_step", "is_gpu_event", "runtime_exclusive", "runtime_total"]
    df = pd.DataFrame(columns=columns)
    pids = [0]
    rids = [559]
    for pid in pids:
        for rid in rids:
            print("start to query rank {}".format(rid))
            t0 = time.clock()
            jx9_filter = "function($record) { return $record.pid == %d &&" \
                         "$record.rid == %d && $record.io_step == %d; }" % (pid, rid, 247)
            records = [json.loads(x) for x in collection.filter(jx9_filter)]
            t1 = time.clock() - t0
            print(records)
            #print("done query rank {} and got {} records in {:.2f} seconds".format(rid, len(records), t1))
            #print("transform to dataframe...")
            #for id, record in enumerate(records):
            #    if id % 100 == 0:
            #        print("record {} of {}".format(id, len(records)))
            #    new_record = {k: record.get(k, None) for k in columns}
            #    df = df.append(new_record, ignore_index=True)
            #df.to_excel("rank_{}.xlsx".format(rid))
            #print("done")

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
