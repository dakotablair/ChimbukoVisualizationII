# ChimbukoVisualizationII

Scalable Visualization Module for Chimbuko

[![Build Status](https://travis-ci.org/CODARcode/ChimbukoVisualizationII.svg?branch=master)](https://travis-ci.org/CODARcode/ChimbukoVisualizationII)

## Overview 

![Overview](./data/images/interface.png)

The visualization module of Chimbuko provides a real-time inspection of the identified anomalous performance behaviors. It receives rank-wise statistics streams from Chimbuko anomaly detection module. It also serves as the interface to query back end provenance database online for a deeper investigation of function executions in selected time intervals. This module consists of two major components as below.

### In-situ Performance Statistics Visualization
* `Dynamic Top MPI Ranks and CPU/GPU Counters`: Streaming data from the anomaly detection module is processed into a number of anomaly statistics including the average, standard deviation, maximum, minimum and the total number of anomalous function executions. Users can select a statistic along with the number of ranks for which it is visualized. A dynamic “ranking dashboard" of the most problematic MPI ranks in a rank-level granularity is provided. A predefined list of CPU/GPU counters is also presented as additional information.
* `Selected Rank History`: Selecting corresponding ranks activates the visualization server to broadcast the number of anomalies per time frame (e.g., per second) of these ranks to the connected users while performance traced applications are running. This streaming scatter plot serves as a time frame-level granularity by showing the dynamic changes of anomaly amount of a MPI rank within a time interval. 

### Online Detailed Functions Visualization
For a selected time interval, this visualization is designed to retrieve data from the provenance database and show the function execution details. It consists of two parts: a function view and a timeline view.
* `Projection of Function Executions`: In the function view, it visualizes the distribution of functions executed within a selected time interval. The distribution can be controlled by selecting the X- and Y-axis among different function properties. This panel can be zoomed and paned to provide convenient interaction.
* `Timeline and Message Communication Visualization`: In the timeline view, users can more closely investigate a selected function execution in details. The invocation relationships among functions (call stacks), adjacent functions in the same time interval, and their communications over other ranks are presented for users to interpret the potential cause of the anomalous behavior. The range of the timeline can be user defined and dragged along to enhance the visualization of short function executions.

## Installation

This package needs to pre-install [py-sonata](https://xgitlab.cels.anl.gov/sds/py-sonata) as the distributed database that requires [spack](https://spack.io/) and [sonata](https://xgitlab.cels.anl.gov/sds/sonata). The visualization module itself depends on a series of packages that are specified in `requirements.txt`. We provide instructions for different platforms: linux, docker, and OLCF Summit.

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
OLCF Summit uses IBM Power System so extra cares might be necessary when installing the toolkit. We need to create a spack virtual environment and our own virtual environment in order to conveniently run jobs in compute nodes.
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
