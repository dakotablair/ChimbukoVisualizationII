#!/usr/bin/env bash

ROOT_DIR=$(pwd)

echo "create db..."
python3 manager.py createdb

# run Redis
./webserver/run-redis.sh &
sleep 1

# run Celery
# python3 manager.py celery --loglevel=info &
python3 manager.py celery --concurrency=1 &
sleep 1

# run test or webserver
python3 manager.py test
# ws_pid=$!

echo "checkpoint"

# wait until test is completed or webserver is shutdown
# wait $ws_pid

# kill celery
pkill -9 -f 'celery worker'

# shut down redis
./webserver/shutdown-redis.sh