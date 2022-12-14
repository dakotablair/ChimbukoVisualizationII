# ChimbukoVisualizationII

Scalable Visualization Module for Chimbuko

[![Build Status](https://travis-ci.org/CODARcode/ChimbukoVisualizationII.svg?branch=master)](https://travis-ci.org/CODARcode/ChimbukoVisualizationII)

## Overview 

![Overview](./data/images/new interface 2.png)

The visualization module of Chimbuko provides a real-time inspection of the identified anomalous performance behaviors. It receives anomalous function streams from Chimbuko anomaly detection module while the application or workflow is still running. It presents as a multi-scale interactive visualization platform that allows users to learn different levels of details about the anomalies. It also serves as the interface to query back end provenance database online and perform a deeper investigation of function executions. This module consists of two major components as below.

### In-situ Performance Statistics Visualization
* `Dynamic Top MPI Ranks and Functions` (top left): Streaming data from the anomaly detection module is aggregated in the back end into two separate statistics about the application or workflow's overall performance in the current timeframe. The first statistics shows the top N ranks that have most anomalous functions. The other statistics shows the top N anomalous functions that happen at most ranks. These two series of bar graphs present as a dynamic ranking dashboard and highlight the ranks and functions that are most problemtic and users should pay attention to. Users can select how many (N) ranks and function to keep track of. Interactive operations are also supported for users to click any top rank/function and see more details about what the anomalies are for that time interval.
* `Dynamic Ranks and Functions Distributions` (top middle): This panel shows the corresponding global distribution of the top N rank/function as line plots. It presents as a supplementary view of not just the top problematic locations of the application or workflow, but also the overall anomaly distribution for both ranks and functions. Users can click any data point of the line plot to find what the corresponding anomalies are.
* `Provenance Database Query` (top right): This panel serves as the interface for users to enter filtering conditions to query the provenance database. Like mentioned above, users have the option to click the two dynamic panels or directly input the function execution information in this panel. All the queried results will be visualized in the next panels as a platform for the drill-down study by the users.

### Online Detailed Functions Visualization
This visualization is designed to retrieve data from the provenance database and show the function execution details. It consists of two parts: a function view and a timeline view.
* `Projection of Function Executions`: In the function view, it visualizes the distribution of functions executed within a selected time interval. The distribution can be controlled by selecting the X- and Y-axis among different function properties. This panel can be zoomed and paned to provide convenient interaction. We support the axis selection using anomaly metrics such as severity and score, and other function related information.
* `Timeline and Message Communication Visualization`: In the timeline view, users can more closely investigate a selected function execution in details. The invocation relationships among functions (call stacks), adjacent functions in the same time interval, and their communications over other ranks are presented for users to interpret the potential cause of the anomalous behavior. The range of the timeline can be user defined and dragged along to enhance the visualization of short function executions.

## Installation

This framework is a web-based application. For the back end, it was developed with `Python3.x` and `Flask`. In order to provide a scalable web service supporting asynchronous processing, `uwsgi`, `Celery`, `Redis` and `Socket IO` were adopted. For the front end, it was developed with `Javascript`, `React` and `D3.js`. These dependencies are specified in `requirements.txt` and can be conveniently installed through `pip3`. 

In order to connect to the Provenance database of Chimbuko where all the actual function execution data are stored, [`py-sonata`](https://xgitlab.cels.anl.gov/sds/py-sonata) needs to be installed as well. It requires both [spack](https://spack.io/) and [sonata](https://xgitlab.cels.anl.gov/sds/sonata). 

We summarize the necessary steps and provide installation instructions for different platforms: linux, docker, and OLCF Summit.

### Linux
* Install spack
```bash
$ git clone https://github.com/spack/spack.git
$ cd spack/bin
$ ./spack install zlib
```

* Install sonata
```bash
$ git clone https://xgitlab.cels.anl.gov/sds/sds-repo.git
$ spack repo add sds-repo
$ spack install mochi-sonata
```
Here you may need to add path for C and gfortran compiler in `.spack/linux/compilers.yaml` if the installation fails.

* Install py-sonata
```bash
$ spack install py-mochi-sonata
```

* Install the visualization package
The back end of our package was developed in python3. Make sure you have that installed before the following steps.
```bash
$ git clone https://github.com/CODARcode/ChimbukoVisualizationII
$ pip3 install --upgrade -r requirements.txt
```

### Docker
* Go to the docker directory where dockerfile is located, say we choose the docker image name `cv2`.
```bash
$ docker build -t cv2 .
```

* Run the docker image to create an interactive container `cv2-test` with port forwarding and attach the volume for sample data, where the destination port is `80` and the volume is located at `~/data`. The volume will be attached to `/Downloads`.
```bash
$ docker run -p 80:5002 -it -v ~/data:/Downloads --name cv2-test cv2
```

* In the container, copy data from `/Downloads` to the `data` directory under `ChimbukoVisualizationII`.
```bash
$ cd ChimbukoVisualizationII
$ cp -r /Downloads/* data/
```

* You may also want to make sure that `redis` is installed. The following commands will download the stable version, compile and run the redis server. If everything goes well, you can terminate the redis by `ctrl+c`.
```bash
$ cd ChimbukoVisualizationII
$ ./webserver/run-redis.sh
```

### Summit
OLCF Summit uses IBM Power System so extra cares might be necessary when installing the toolkit. We need to create a spack virtual environment and our own virtual environment in order to conveniently run jobs in compute nodes. In this example, we use `$HOME` directory to install spack and the environments.
* Install spack
```bash
$ git clone https://github.com/spack/spack.git
$ . spack/share/spack/setup-env.sh
```

* Install sonata and add platform-configurations
```bash
$ git clone https://xgitlab.cels.anl.gov/sds/sds-repo.git
$ spack repo add sds-repo
$ git clone https://xgitlab.cels.anl.gov/sds/experiments/platform-configurations.git
$ cd platform-configurations/ORNL/Summit
```
Open the file `spack.yml` to edit the path of `sds-repo` to match your installation. If you want to use `tcp` as your database server protocol, you also need to edit line 61 and add `tcp` to the fabrics.

* Create spack environment and install py-sonata
```bash
$ spack env create pysonata_env spack.yaml
```
The new spack env `pysonata_env` has been created and activated. Now we need to add py-sonata.
```bash
$ spack add py-mochi-sonata%gcc@9.1.0
$ spack install
```
The spack environment has been installed. You can use the commands below to activate and deactivate:
```bash
$ spack env activate pysonata_env
$ despacktivate
```

* Install visualization package by creating a python virtual environment in Summit. Summit has suggestions about how to create python3 virtual environment. By following the instruction, we need to create corresponding directories under `$HOME` and create environment.
```bash
$ VENVS="${HOME}/summit/opt/venvs"
$ python3 -m venv "${VENVS}/chimbuko_pysonata_vis_venv"
$ . $VENVS/chimbuko_pysonata_vis_venv/bin/activate
```

* Then when the venv is activated, we can install the packages:
```bash
$ git clone https://github.com/CODARcode/ChimbukoVisualizationII
$ cd ChimbukoVisualizationII
$ pip3 install -r requirements
$ ./webserver/run-redis.sh
```

## Execution
### Linux
* Under the main directory `ChimbukoVisualizationII`, run the webserver with:
```bash
$ ./webserver/run_webserver.sh &
```
When the terminal prompts `wsgi starting up on http://0.0.0.0:5002`, that indicates the webserver is ready. You can then open a browser and type below to see the main GUI (the same as the overview image):
```bash
localhost:5002
```
You can modify the parameter setting in this script for `celery` worker number, test data path, and provenance database protocol. More can be found under [Chimbuko](https://github.com/CODARcode/Chimbuko) repo.

* Shut down the server with:
```bash
./webserver/shutdown_webserver.sh
```

### Docker
* load py-sonata module:
```bash
$ source /spack/spack/share/spack/setup-env.sh && spack load py-mochi-sonata
```

* Docker user by default is superuser (root). But celery worker can not be ran by superuser. Add below to bypass this contraint.
```bash
$ export C_FORCE_ROOT="true"
```

* Under the main directory `ChimbukoVisualizationII`, run the webserver with:
```bash
$ ./webserver/run_webserver.sh &
```
When the terminal prompts `wsgi starting up on http://0.0.0.0:5002`, that indicates the webserver is ready. Since we did port forwarding, you can then open a browser and type below to see the main GUI (the same as the overview image):
```bash
localhost:80
```

* If you have attach the data volume that contains simulation dataset, you can click `RUN SIMULATION` to have the simulation executes that mimics the in-situ performance anomaly detection and query the database to check function details.

* Shut down the server with:
```bash
$ ./webserver/shutdown_webserver.sh
```

### Summit login/launch node
* To run our module at login or launch node in the interactive mode, the process is quite similar to Docker. You need to load modules, run webserver and finally do port forwarding to check the GUI in a brower. Here, `$HOME` is your directory where spack, sonata and vis virtual environment were installed.
```bash
$ . $HOME/spack/share/spack/setup-env.sh
$ spack env activate pysonata_env
$ . $HOME/summit/opt/venvs/chimbuko_pysonata_vis_venv/activate
```

* Under the main directory `ChimbukoVisualizationII`, run the webserver with:
```bash
$ ./webserver/run_webserver.sh &
```
When the terminal prompts `wsgi starting up on http://0.0.0.0:5002`, that indicates the webserver is ready. We need to do port forwarding as below by opening another terminal:
```bash
$ ssh -t -L 80:node_name.summit.olcf.ornl.gov:5002 account@summit.olcf.ornl.gov
```
Then you can then open a browser and type below to see the main GUI (the same as the overview image):
```bash
localhost:80
```

* If you have copied the simulation dataset under `ChimbukoVisualizationII/data` and set up the parameters properly in `ChimbukoVisualizationII/webserver/run_webserver.sh`, you can click `RUN SIMULATION` to have the simulation executes that mimics the in-situ performance anomaly detection and query the database to check function details.

* Shut down the server in the first terminal with:
```bash
$ ./webserver/shutdown_webserver.sh
```

### Summit compute node
If you want to do job submission and run the program on the compute node, we have provided an example script for you to try conveniently. After installing, go to the main directory `ChimbukoVisualizationII`. Open script `run_vis.lsf` and make sure in lines 14, 17, 23 and 36, all the paths are set up correctly. Then simply run the following command, the webserver will be up for 5 minutes and shut up automatically.
```bash
$ bsub run_vis.lsf
```

### Sending HTTP Requests
While the webserver is up, it can accept `POST` method requests to the url of `http://0.0.0.0:5002/api/anomalydata` with data in the `json` format. The detailed format schema can be found [here](https://chimbuko-performance-analysis.readthedocs.io/en/latest/io_schema/schema.html#parameter-server-streaming-output). An example `python` implementation is as below:
```python
import requests

payload = {'anomaly_stats': {...},
           'counter_stats': [...]}
resp = requests.post(url=url, json=payload)
print(resp)
```

The data is expected to be the anomaly statistics and CPU/GPU counters associated with certain workflow. While the requests streaming in, the front end visualization in the browser will visualize and update the statistics in real-time. As long as the back end provenance database is up and contains the corresponding function executions of the workflow, users can query the database for more details by interacting with the front end interface.

## Unit test
After installation and loading dependent modules, similar to the execution, unit test can be done after entering the main directory as below:
```bash
$ ./webserver/run_test.sh
```

More details can be found in [Chimbuko](https://github.com/CODARcode/Chimbuko) repo.
