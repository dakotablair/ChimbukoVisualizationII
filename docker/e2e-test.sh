#!/bin/bash

set -eux pipefail

env

ls -halF $RUN_DIR

pushd $RUN_DIR
git config --global --add safe.directory $RUN_DIR
git checkout actions_unstable

mkdir -p data/grid
ln -s /Downloads/repeat_1rank data/grid/

# Install Redis

function hold_for_redis () {
  OUTPUT="";
  while [ "$OUTPUT" != "PONG" ]; do
    OUTPUT=`./redis-stable/src/redis-cli PING`;
    echo hold on 1 sec
    sleep 1
  done
}

./webserver/run-redis.sh &

pushd /opt/spack-environment/ && \
    source /spack/spack/share/spack/setup-env.sh && \
    spack env activate .
popd

python -m pip install -r requirements.large.txt
python -m pip install -r requirements.txt

hold_for_redis

popd

CHIMBUKO_VIZ_ROOT=$RUN_DIR ./run.sh

set +ex
