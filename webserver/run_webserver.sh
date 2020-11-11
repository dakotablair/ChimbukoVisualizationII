#!/usr/bin/env bash

ROOT_DIR=$(pwd)
WORK_DIR="${ROOT_DIR}/data"
cd "${WORK_DIR}" #cd command must use doublequote to take space in filename

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
export SIMULATION_JSON="${WORK_DIR}/${DATA_NAME}/stats/"

echo "run redis ..."
cd "$ROOT_DIR"
webserver/run-redis.sh &
sleep 10

echo "run celery ..."
python3 manager.py celery --loglevel=info &
sleep 10

echo "run db ..."
python3 manager.py createdb --drop_first='True' &
sleep 10

echo "run webserver ..."
python3 manager.py runserver --host 0.0.0.0 --port 5002 --debug



