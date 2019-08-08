#!/usr/bin/env bash
module load gcc/8.1.1
module load python/3.7.0-anaconda3-5.3.0

source activate chimbuko_viz

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

echo "checkpoint"

# wait until test is completed or webserver is shutdown
# wait $ws_pid

# kill celery and redis
echo "Finalize visualization server ... "

echo "shutdown celery workers ..."
# need a way to shutdonw gracefully...
# python3 manager.py celery control shutdown (didn't work)
pkill -9 -f 'celery worker'

echo "showdown redis server ..."
./webserver/shutdown-redis.sh

