#!/usr/bin/env bash

ROOT_DIR=$(pwd)
WORK_DIR="${ROOT_DIR}/data"
cd "${WORK_DIR}" #cd command must use doublequote to take space in filename

# for sample data
#SAMPLE_TAR="${WORK_DIR}/sample.tar.gz"
#if [ ! -d "${WORK_DIR}/logs" ]; then
#    rm -rf ${WORK_DIR}/logs
#    rm -rf ${WORK_DIR}/executions
#    tar -xzvf $SAMPLE_TAR
#fi
#DB_DIR="logs"
#DATA_NAME="."

# for data from summit
DATA_NAME="nwchem-104-8-SST"
DATA_TAR="${WORK_DIR}/${DATA_NAME}.tar.gz"
if [ ! -d "${WORK_DIR}/${DATA_NAME}" ]; then
    tar -xzvf "$DATA_TAR"
fi
DB_DIR="${DATA_NAME}/db"


# server config
export SERVER_CONFIG="production"
export DATABASE_URL="sqlite:///${WORK_DIR}/${DB_DIR}/main.sqlite"
export ANOMALY_STATS_URL="sqlite:///${WORK_DIR}/${DB_DIR}/anomaly_stats.sqlite"
export ANOMALY_DATA_URL="sqlite:///${WORK_DIR}/${DB_DIR}/anomaly_data.sqlite"
export FUNC_STATS_URL="sqlite:///${WORK_DIR}/${DB_DIR}/func_stats.sqlite"
export EXECUTION_PATH="${WORK_DIR}/${DATA_NAME}/executions"

echo "run redis ..."
cd "$ROOT_DIR"
webserver/run-redis.sh &
sleep 10

echo "run celery ..."
python3 manager.py celery --loglevel=info &
sleep 10

echo "run webserver ..."
python3 manager.py runserver --host 0.0.0.0 --port 5002 --debug



