# Steps

First I cloned the repository locally:

```sh
git clone git@github.com:CODARcode/ChimbukoVisualizationII.git
```

Then, following the docker instructions:

```sh
docker build -t cv2 .
```

fails with the following error messages:

```sh
 > [4/5] RUN cd tests &&     tar xvzf test.tar.gz:
0.201 /bin/bash: line 0: cd: tests: No such file or directory
------
dockerfile:11
--------------------
  10 |
  11 | >>> RUN cd tests && \
  12 | >>>     tar xvzf test.tar.gz
  13 |
--------------------
ERROR: failed to solve: process "/bin/bash -c cd tests &&     tar xvzf test.tar.gz" did not complete successfully: exit code: 1
```

After adjusting `dockerfile`:

```diff
-RUN git clone -b master https://github.com/celiafish/ChimbukoVisualizationII.git && \
-    cd ChimbukoVisualizationII && \
+RUN git clone -b master https://github.com/celiafish/ChimbukoVisualizationII.git /ChimbukoVisualizationII && \
+    cd /ChimbukoVisualizationII && \
```

The image will now build.

```sh
docker run -p 80:5002 -it -v ~/data:/Downloads --name cv2-test cv2
```

> In the container, copy data from `/Downloads` to the data directory under
> `ChimbukoVisualizationII`.

There is no data in `/Downloads` directory inside the container. This data is
expected to be in `~/data` on the host filesystem, but I do not have that data.

As a result, this operation copies nothing:
```sh
cd /ChimbukoVisualizationII
cp -r /Downloads/* data/
```

The next step allows redis to run as a superuser:

```sh
export C_FORCE_ROOT="true"                                                                                                    [14/271]
```

Attempting to run the server now fails with the following error messages:

```sh
$ ./webserver/run_webserver.sh
Chimbuko Services: viz is obtaining provDB addresses from path
create db ...
ProvDB:__init__ started
ProvDB initialization commencing with parameters  pdb_path=/ChimbukoVisualizationII/data/grid/repeat_1rank/chimbuko.304740/provdb/  pdb_sharded_num=1  pdb_addr= pdb_addr_path= pd
b_ninstance=4
[2024-11-14 13:30:10.183] [error] [provider:0] Error when attaching database provdb.0 of type unqlite:
[2024-11-14 13:30:10.183] [error] [provider:0]    => Database file /ChimbukoVisualizationII/data/grid/repeat_1rank/chimbuko.304740/provdb/provdb.0.unqlite does not exist
Traceback (most recent call last):
  File "manager.py", line 10, in <module>
    from server import create_app, db, socketio
  File "/ChimbukoVisualizationII/server/__init__.py", line 18, in <module>
    pdb_addr_path=os.environ.get('PROVDB_ADDR_PATH', '')
  File "/ChimbukoVisualizationII/server/provdb.py", line 34, in __init__
    % file_name)
RuntimeError: Database file /ChimbukoVisualizationII/data/grid/repeat_1rank/chimbuko.304740/provdb/provdb.0.unqlite does not exist
Exception ignored in: <bound method ProvDB.__del__ of <server.provdb.ProvDB object at 0x7f00930314e0>>
Traceback (most recent call last):
  File "/ChimbukoVisualizationII/server/provdb.py", line 127, in __del__
    if self.pdb_databases:
AttributeError: 'ProvDB' object has no attribute 'pdb_databases'
```

