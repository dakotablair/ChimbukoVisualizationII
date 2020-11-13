#!/usr/bin/env bash

ROOT_DIR=$(pwd)
WORK_DIR="${ROOT_DIR}/data"
cd "${WORK_DIR}" #cd command must use doublequote to take space in filename

# for test data
DATA_NAME="sample"
export PROVENANCE_DB="${WORK_DIR}/${DATA_NAME}/provdb/"
export SHARDED_NUM=1

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