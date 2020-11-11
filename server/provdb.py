import pymargo
from pymargo.core import Engine
from pysonata.provider import SonataProvider
from pysonata.client import SonataClient
from pysonata.admin import SonataAdmin


class ProvDB():
    def __init__(self, pdb_path='', pdb_sharded_num=1):
        self.pdb_engine = Engine('na+sm', pymargo.server)
        self.pdb_provider = SonataProvider(self.pdb_engine, 0)
        self.pdb_address = str(self.pdb_engine.addr())
        self.pdb_admin = SonataAdmin(self.pdb_engine)
        self.pdb_client = SonataClient(self.pdb_engine)

        self.pdb_names = []
        self.pdb_collections = []

        for i in range(pdb_sharded_num):
            pdb_name = 'provdb.' + str(i)
            self.pdb_names.append(pdb_name)
            file_name = pdb_path + pdb_name + '.unqlite'
            self.pdb_admin.attach_database(self.pdb_address, 0, pdb_name,
                                           'unqlite',
                                           "{ \"path\" : \"%s\" }" % file_name)
            pdb = self.pdb_client.open(self.pdb_address, 0, pdb_name)
            self.pdb_collections.append(pdb.open('anomalies'))

    def __del__(self):
        for name in self.pdb_names:
            self.pdb_admin.detach_database(self.pdb_address, 0, name)
        del self.pdb_provider
        self.pdb_engine.finalize()
        print("Provdb connection shut down!")
