#!/usr/bin/env bash
set -x
source /spack/share/spack/setup-env.sh
cd /opt/cv2
spack env activate .
python3.8 -m pip install -r /requirements.txt
python3.8 -m pip install "pip==24" pkgconfig setuptools wheel --upgrade
python3.8 -m pip install git+https://github.com/mochi-hpc/py-mochi-sonata.git@v0.1.2
