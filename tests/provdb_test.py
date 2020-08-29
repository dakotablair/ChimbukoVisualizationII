import sys
import json

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
    jx9_filter = "function($record) { return $record.is_gpu_event == True; }"
    filtered_records = [ json.loads(x) for x in collection.filter(jx9_filter) ]
    print("There are", len(filtered_records), "records that are GPU events.")
    print("The first one is:")
    print(filtered_records[0])

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