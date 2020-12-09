#!/usr/bin/env bash
# module load gcc/9.1.0
# module load python/3.7.0

# . /ccs/home/wxu/spack/share/spack/setup-env.sh
# spack env activate pysonata_env
# spack load -r py-mochi-sonata
# . /ccs/proj/csc299/wxu/summit/opt/venvs/chimbuko_pysonata_vis_venv/bin/activate

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

echo "Finalize visualization server ... "

echo "shutdown celery workers ..."
# need a way to shutdonw gracefully...
# python3 manager.py celery control shutdown (didn't work)
pkill -9 -f 'celery worker'

echo "showdown redis server ..."
./webserver/shutdown-redis.sh

