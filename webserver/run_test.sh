#!/usr/bin/env bash
source /spack/spack/share/spack/setup-env.sh
spack load py-mochi-sonata
export C_FORCE_ROOT=1

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