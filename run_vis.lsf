#!/bin/bash
# BEGIN LSF Directives
#BSUB -P CSC299
#BSUB -W 5
#BSUB -nnodes 1
#BSUB -J pysonata-chimvis
#BSUB -o pysonata-chimvis.o.%J
#BSUB -e pysonata-chimvis.e.%J
#BSUB -alloc_flags "smt4"

module load gcc/9.1.0
module load python/3.7.0

. /ccs/home/wxu/spack/share/spack/setup-env.sh
spack env activate pysonata_env
spack load -r py-mochi-sonata
. /ccs/proj/csc299/wxu/summit/opt/venvs/chimbuko_pysonata_vis_venv/bin/activate

#pip list

#set -x

CODAR=/ccs/proj/csc299/wxu

# CHIMBUKO (visualization)
export CHIMBUKO_VIS_ROOT=$CODAR/ChimbukoVisualizationII
export CHIMBUKO_VIS_DATA=$CHIMBUKO_VIS_ROOT/data

echo ""
echo "==========================================="
echo "Set working directory"
echo "==========================================="
BATCH_DIR=`pwd`
echo "BATCH_DIR: $BATCH_DIR"

WORK=/gpfs/alpine/csc299/proj-shared/wxu
cd $WORK
rm -rf chimvis2
mkdir -p chimvis2
cd chimvis2
mkdir logs
mkdir db
mkdir stats
mkdir provdb
WORK_DIR=`pwd`
echo "WORK_DIR: $WORK_DIR"

echo ""
echo "=========================================="
echo "User inputs"
echo "=========================================="
export DATA_NAME="96rank_sharded_vizdump"
export SHARDED_NUM=20
export PROVDB_ADDR=""

echo ""
echo "==========================================="
echo "Config VIS SERVER"
echo "==========================================="
export SERVER_CONFIG="production"
export DATABASE_URL="sqlite:///${WORK_DIR}/db/main.sqlite"
export ANOMALY_STATS_URL="sqlite:///${WORK_DIR}/db/anomaly_stats.sqlite"
export ANOMALY_DATA_URL="sqlite:///${WORK_DIR}/db/anomaly_data.sqlite"
export FUNC_STATS_URL="sqlite:///${WORK_DIR}/db/func_stats.sqlite"
export PROVENANCE_DB="${WORK_DIR}/provdb/"
export SIMULATION_JSON="${WORK_DIR}/stats/"
export CELERY_BROKER_URL="redis://"

echo ""
echo "==========================================="
echo "Copy binaries & data to ${WORK_DIR}"
echo "==========================================="
cp -r $CHIMBUKO_VIS_DATA/$DATA_NAME/provdb/* provdb
cp -r $CHIMBUKO_VIS_DATA/$DATA_NAME/stats/* stats
cp -r $CHIMBUKO_VIS_ROOT/redis-stable/redis.conf .
cp -r $CHIMBUKO_VIS_ROOT .
mv ChimbukoVisualizationII viz

sed -i "365s|dir ./|dir ${WORK_DIR}/|" redis.conf
sed -i "68s|bind 127.0.0.1|bind 0.0.0.0|" redis.conf
sed -i "224s|daemonize no|daemonize yes|" redis.conf
sed -i "247s|pidfile /var/run/redis_6379.pid|pidfile ${WORK_DIR}/redis.pid|" redis.conf
sed -i "260s|logfile "\"\""|logfile ${WORK_DIR}/logs/redis.log|" redis.conf
sed -i "264s|syslog-enabled no|syslog-enabled yes|" redis.conf

if true; then
  echo ""
  echo "==========================================="
  echo "Launch Chimbuko visualization server"
  echo "==========================================="
  cd $WORK_DIR/viz
  jsrun -n 1 -a 1 -c 1 -g 0 -r 1 ${BATCH_DIR}/run_webserver_summit.sh "${WORK_DIR}/logs" \
  	  "--loglevel=info --pool=gevent --concurrency=5" \
          5002 ${WORK_DIR}/redis.conf &

  while [ ! -f webserver.host ];
  do
    sleep 1
  done
  WS_HOST=$(<webserver.host)
  while [ ! -f webserver.port ];
  do
    sleep 1
  done
  WS_PORT=$(<webserver.port)
  echo "WS_HOST: $WS_HOST"
  echo "WS_PORT: $WS_PORT"
fi

sleep 180

if true; then
echo ""
echo "==========================================="
echo "Shutdown Chimbuko visualization server"
echo "==========================================="
cd $WORK_DIR/viz
jsrun -n 1 -a 1 -c 1 -g 0 -r 1 ${BATCH_DIR}/shutdown_webserver_summit.sh ${WS_HOST} ${WS_PORT}
fi

rm -rf viz

echo "Bye~~!!"