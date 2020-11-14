#!/usr/bin/env bash

curl -X GET http://0.0.0.0:5002/tasks/inspect
curl -X GET http://0.0.0.0:5002/stop
pkill -9 -f 'celery worker'
webserver/shutdown-redis.sh
