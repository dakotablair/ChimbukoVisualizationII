import pymargo
from pymargo.core import Engine
from pysonata.provider import SonataProvider
from pysonata.client import SonataClient
from pysonata.admin import SonataAdmin

import gc


class ProvDB():
    def __init__(self, pdb_path='', pdb_sharded_num=0, pdb_addr=''):
        if pdb_addr == '':  # Standalone mode, need to create engine provider
            self.pdb_engine = Engine('na+sm', pymargo.server)
            self.pdb_provider = SonataProvider(self.pdb_engine, 0)
            self.pdb_address = str(self.pdb_engine.addr())
            self.pdb_admin = SonataAdmin(self.pdb_engine)
            self.pdb_client = SonataClient(self.pdb_engine)

            if pdb_path and int(pdb_sharded_num) > 0:
                for i in range(int(pdb_sharded_num)):
                    pdb_name = 'provdb.' + str(i)
                    file_name = pdb_path + pdb_name + '.unqlite'
                    self.pdb_admin.attach_database(self.pdb_address, 0,
                                                   pdb_name,
                                                   'unqlite',
                                                   "{ \"path\" : \"%s\" }"
                                                   % file_name)
        else:  # Other Chimbuko module created the engine
            self.pdb_engine = Engine(pdb_addr.split(':')[0], pymargo.client)
            self.pdb_address = pdb_addr
            self.pdb_client = SonataClient(self.pdb_engine)

        self.pdb_collections = []
        self.pdb_names = []
        for i in range(pdb_sharded_num):
            pdb_name = 'provdb.' + str(i)
            self.pdb_names.append(pdb_name)
            pdb = self.pdb_client.open(self.pdb_address, 0, pdb_name)
            col = pdb.open('anomalies')
            self.pdb_collections.append(col)

        print("=-=-=-=-=Initiated ProvDB instance {}=-=-=-=-=".format(
            self.pdb_address))

    def __del__(self):
        if self.pdb_collections:
            for col in self.pdb_collections:
                del col
                col = None
            del self.pdb_collections
            self.pdb_collections = []
        if self.pdb_names:
            for name in self.pdb_names:
                if hasattr(self, 'pdb_admin'):
                    self.pdb_admin.detach_database(self.pdb_address,
                                                   0, name)
                del name
                name = None
            self.pdb_names = []
        if self.pdb_client:
            del self.pdb_client
            self.pdb_client = None
        if self.pdb_address:
            del self.pdb_address
            self.pdb_address = None
        if hasattr(self, 'pdb_admin') and self.pdb_admin:
            del self.pdb_admin
            self.pdb_admin = None
        if hasattr(self, 'pdb_provider') and self.pdb_provider:
            del self.pdb_provider
            self.pdb_provider = None
        if self.pdb_engine:
            self.pdb_engine.finalize()
            gc.collect()
            del self.pdb_engine
            self.pdb_engine = None
        print("=-=-=-=-=Finished Provdb instance deletion=-=-=-=-=")
