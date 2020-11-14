#!/usr/bin/env bash
uwsgi --http 127.0.0.1:5002 --wsgi-file server/wsgi.py
