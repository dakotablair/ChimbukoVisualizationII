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
DATA_NAME="96rank_sharded_vizdump"

# server config
export SERVER_CONFIG="production"
export DATABASE_URL="sqlite:///${WORK_DIR}/${DATA_NAME}/db/main.sqlite"
export ANOMALY_STATS_URL="sqlite:///${WORK_DIR}/${DATA_NAME}/db/anomaly_stats.sqlite"
export ANOMALY_DATA_URL="sqlite:///${WORK_DIR}/${DATA_NAME}/db/anomaly_data.sqlite"
export FUNC_STATS_URL="sqlite:///${WORK_DIR}/${DATA_NAME}/db/func_stats.sqlite"
export PROVENANCE_DB="${WORK_DIR}/${DATA_NAME}/provdb/"
export SHARDED_NUM=20
# export PROVDB_ADDR="ofi+tcp;ofi_rxm://172.17.0.2:32903"
export SIMULATION_JSON="${WORK_DIR}/${DATA_NAME}/stats/"

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



