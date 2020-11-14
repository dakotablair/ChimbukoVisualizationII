#!/usr/bin/env bash

ROOT_DIR=$(pwd)
WORK_DIR="${ROOT_DIR}/data"

# for test data
DATA_NAME="test"
export PROVENANCE_DB="${WORK_DIR}/${DATA_NAME}/"
export SHARDED_NUM=1
export DATABASE_URL="sqlite:///${WORK_DIR}/${DATA_NAME}/main.sqlite"
export ANOMALY_STATS_URL="sqlite:///${WORK_DIR}/${DATA_NAME}/anomaly_stats.sqlite"
export ANOMALY_DATA_URL="sqlite:///${WORK_DIR}/${DATA_NAME}/anomaly_data.sqlite"
export FUNC_STATS_URL="sqlite:///${WORK_DIR}/${DATA_NAME}/func_stats.sqlite"

# run Redis
./webserver/run-redis.sh &
sleep 1

# run Celery
# python3 manager.py celery --loglevel=info &
python3 manager.py celery &
sleep 1

# run test or webserver
python3 manager.py test
# ws_pid=$!

# echo "checkpoint"

# wait until test is completed or webserver is shutdown
# wait $ws_pid

# kill celery and redis
#echo "shutdown server ..."
#./webserver/shutdown_webserver.sh