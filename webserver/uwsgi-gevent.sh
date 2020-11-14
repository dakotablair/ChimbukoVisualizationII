#!/usr/bin/env bash
#uwsgi --gevent 100 --http 127.0.0.1:5002 --wsgi-file server/wsgi.py
uwsgi --http 127.0.0.1:5002 \
      --http-websockets \
      --master \
      --wsgi-file server/wsgi.py \
      --master \
      --gevent 500 \
      --callable app