import pymargo
from pymargo.core import Engine
from pysonata.provider import SonataProvider
from pysonata.client import SonataClient
from pysonata.admin import SonataAdmin

import gc


class ProvDB():
    def __init__(self, pdb_path='', pdb_sharded_num=0, pdb_addr='', pdb_addr_path='', pdb_ninstance=1):
        print("ProvDB:__init__ started")
        print("ProvDB initialization commencing with parameters  pdb_path=%s  pdb_sharded_num=%d  pdb_addr=%s pdb_addr_path=%s pdb_ninstance=%d" % (pdb_path, int(pdb_sharded_num), pdb_addr, pdb_addr_path, int(pdb_ninstance)) )
        self.pdb_shard_map = []  #A map of shard index to a tuple of (server instance, provider index)
        self.pdb_ninstance = int(pdb_ninstance)

        if pdb_addr == '' and pdb_addr_path == '':  # Standalone mode, need to create engine provider
            #Argument of number of server instances is ignored here
            self.pdb_engine = [ Engine('ofi+tcp', mode=pymargo.server) ]
            self.pdb_provider = [ SonataProvider(self.pdb_engine, 0) ]
            self.pdb_address = [ str(self.pdb_engine.addr()) ]
            self.pdb_admin = [ SonataAdmin(self.pdb_engine) ]
            self.pdb_client = [ SonataClient(self.pdb_engine) ]

            provider = 0 #All databases attached to the same provider
            if pdb_path and int(pdb_sharded_num) > 0:
                for i in range(int(pdb_sharded_num)):
                    pdb_name = 'provdb.' + str(i)
                    file_name = pdb_path + pdb_name + '.unqlite'
                    self.pdb_admin[0].attach_database(self.pdb_address[0], provider,
                                                   pdb_name,
                                                   'unqlite',
                                                   "{ \"path\" : \"%s\" }"
                                                   % file_name)
                    #For offline mode all shards are attached to server instance 0, provider 0
                    self.pdb_shard_map.append( (0,0) )

        else: 
            # Other Chimbuko module created the engine
            # Either an address is supplied as pdb_addr (#instance must be 1)
            # or a pdb_addr_path is set to the directory containing the provDB setup output (in which case pbd_addr is ignored)
            if self.pdb_ninstance == 1 and pdb_addr != '':
                #pdb_addr is the address of the server
                self.pdb_engine = [ Engine(pdb_addr.split(':')[0], pymargo.client) ]
                self.pdb_address = [ pdb_addr ]
                self.pdb_client = [ SonataClient(self.pdb_engine[0]) ]
                print("Attached to single remote server instance on address %s" % self.pdb_address[0])
                for i in range(int(pdb_sharded_num)):
                    self.pdb_shard_map.append( (0,i+1) )   #provider index for server 0 shard i is always i+1  (0 is reserved for the global database)
                
            else:
                #pdb_addr is ignored. pdb_addr_path must be set to the output path of the database where addresses and shard->instance maps are located
                #Path contains provider.map which maps shard -> (instance, provider)     and  provider.address.${i}  which contains the ip:port for server instance i
                if pdb_addr_path == '':
                    raise Exception("pdb_addr_path must be set if #instances>1 or #instances==1 and pdb_addr is not supplied")

                #Parse the map
                f = open("%s/provider.map" % pdb_addr_path,'r')
                for i in range(int(pdb_sharded_num)):
                    line = f.readline()
                    l = line.split()
                    if len(l) != 3:
                        raise Exception("Line \"%s\" in provider.map does not have expected format" % line)
                    if int(l[0]) != i:
                        raise Exception("Line \"%s\" in provider.map does not have expected shard index %d" % (line,i) )
                    self.pdb_shard_map.append( (int(l[1]), int(l[2]) ) )
                f.close()

                #Parse the addresses
                self.pdb_address = []
                for i in range(self.pdb_ninstance):
                    f = open("%s/provider.address.%d" % (pdb_addr_path,i), 'r')
                    self.pdb_address.append(f.readline())
                    f.close()

                #We want the engine to be initialized with the openfabrics provider type used to communicate with the clients (eg ofi+tcp;ofi_rxm)
                #In principle different providers could be used by different server instances so we allow for multiple engines
                engine_ofiprov = []
                instance_engine_map = [] #map address index to engine index
                self.pdb_engine = []
                for a in self.pdb_address:
                    ofiprov=a.split(':')[0]
                    eng_idx = None
                    for e in range(len(engine_ofiprov)):
                        if engine_ofiprov[e] == ofiprov:
                            eng_idx = e
                            break
                    if eng_idx == None:
                        eng_idx = len(engine_ofiprov)
                        print("Creating engine %d with provider %s" % (eng_idx,ofiprov) )
                        self.pdb_engine.append( Engine(ofiprov, pymargo.client) )
                        engine_ofiprov.append(ofiprov)

                    print("Address %s maps to engine index %d" % (a, eng_idx))
                    instance_engine_map.append(eng_idx)
                
                #One client per address
                self.pdb_client = []
                for i in range(self.pdb_ninstance):
                    eng_idx = instance_engine_map[i]
                    self.pdb_client.append( SonataClient(self.pdb_engine[eng_idx]) )
                    print("Attached to remote server instance %d on address %s" % (i,self.pdb_address[i]))


        self.pdb_databases = []
        self.pdb_collections = []
        self.pdb_names = []
        for i in range(pdb_sharded_num):
            pdb_name = 'provdb.' + str(i)
            self.pdb_names.append(pdb_name)
            
            (inst, provider) = self.pdb_shard_map[i]
            if inst < 0 or inst >= self.pdb_ninstance:
                raise Exception("Invalid instance index detected")

            database = self.pdb_client[inst].open(self.pdb_address[inst], provider, pdb_name)
            print("Attached to database shard %d residing on server instance %d and provider %d" % (i,inst,provider))

            self.pdb_databases.append(database)
            col = database.open('anomalies')
            self.pdb_collections.append(col)

        # print("=-=-=-=-=Initiated ProvDB instance {}=-=-=-=-=".format(
        #     self.pdb_address))

    def __del__(self):
        if self.pdb_databases:
            for database in self.pdb_databases:
                del database
                database = None
            del self.pdb_databases
            self.pdb_databases = []
        if self.pdb_collections:
            for col in self.pdb_collections:
                del col
                col = None
            del self.pdb_collections
            self.pdb_collections = []
        if self.pdb_names:
            for i in range(len(self.pdb_names)):
                name = self.pdb_names[i]
                if hasattr(self, 'pdb_admin'):  #Only in offline mode
                    (inst, provider) = self.pdb_shard_map[i]                    
                    self.pdb_admin[inst].detach_database(self.pdb_address[inst],
                                                         provider, name)
                del name
                name = None
            self.pdb_names = []
        if self.pdb_client:
            del self.pdb_client[:]
            self.pdb_client = None
        if self.pdb_address:
            del self.pdb_address[:]
            self.pdb_address = None
        if hasattr(self, 'pdb_admin') and self.pdb_admin:
            del self.pdb_admin[:]
            self.pdb_admin = None
        if hasattr(self, 'pdb_provider') and self.pdb_provider:
            del self.pdb_provider[:]
            self.pdb_provider = None
        if self.pdb_engine:
            for i in range(len(self.pdb_engine)):
                self.pdb_engine[i].finalize()
            gc.collect()
            del self.pdb_engine[:]
            self.pdb_engine = None
        if self.pdb_shard_map:
            del self.pdb_shard_map[:]
            self.pdb_shard_map = None
        # print("=-=-=-=-=Finished Provdb instance deletion=-=-=-=-=\n")
