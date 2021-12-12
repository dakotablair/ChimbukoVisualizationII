#!/usr/bin/env bash
# module load gcc/9.1.0
# module load python/3.7.0

# . /ccs/home/wxu/spack/share/spack/setup-env.sh
# spack env activate pysonata_env
# spack load -r py-mochi-sonata
# . /ccs/proj/csc299/wxu/summit/opt/venvs/chimbuko_pysonata_vis_venv/bin/activate

ROOT_DIR=$(pwd)
WORK_DIR="${ROOT_DIR}/data"
cd "$ROOT_DIR" #cd command must use doublequote to take space in filename

# for test data
DATA_NAME="48rank_100step"

# for sharded n_instance provdb
provdb_ninstances=1
provdb_nshards=1
provdb_writedir="${WORK_DIR}/${DATA_NAME}/provdb/"
provdb_addr_dir=""

# server config
export SERVER_CONFIG="production"
export DATABASE_URL="sqlite:///${WORK_DIR}/${DATA_NAME}/db/main.sqlite"
export ANOMALY_STATS_URL="sqlite:///${WORK_DIR}/${DATA_NAME}/db/anomaly_stats.sqlite"
export ANOMALY_DATA_URL="sqlite:///${WORK_DIR}/${DATA_NAME}/db/anomaly_data.sqlite"
export FUNC_STATS_URL="sqlite:///${WORK_DIR}/${DATA_NAME}/db/func_stats.sqlite"
export SIMULATION_JSON="${WORK_DIR}/${DATA_NAME}/stats/"

# Provide parameters for provenance database
export PROVDB_NINSTANCE=${provdb_ninstances}
export SHARDED_NUM=${provdb_nshards}
export PROVENANCE_DB=${provdb_writedir} #already an absolute path

if (( ${provdb_ninstances} == 1 )); then
    #Simpler instantiation if a single server
    export PROVDB_ADDR=""
    echo "Chimbuko Services: viz is connecting to provDB provider 0 on address" $PROVDB_ADDR
else
    export PROVDB_ADDR_PATH=${provdb_addr_dir}
    echo "Chimbuko Services: viz is obtaining provDB addresses from path" $PROVDB_ADDR_PATH
fi

echo "create db ..."
python3 manager.py createdb

echo "run redis ..."
webserver/run-redis.sh &
sleep 10

echo "run celery ..."
python3 manager.py celery --loglevel=info --pool=gevent --concurrency=5 &
sleep 10

echo "run webserver ..."
python3 manager.py runserver --host 0.0.0.0 --port 5002 --debug



