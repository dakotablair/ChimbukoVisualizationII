#!/usr/bin/env bash
uwsgi --http 127.0.0.1:5000 --wsgi-file server/wsgi.py
