#!/usr/bin/env bash
set -x
source /spack/share/spack/setup-env.sh
spack repo add mochi-spack-packages
mkdir -p /opt/cv2
cd /opt/cv2
spack env create --with-view view --dir .
spack env activate .
spack -e . add mochi-margo
spack -e . add mochi-sonata
spack -e . add mpich
spack -e . add "python@3.8.18"
spack -e . add py-mochi-margo # requires python3.11?
spack -e . add py-pip
# spack -e . add py-setuptools
spack -e . concretize
spack -e . install

# python3.11 -m pip install setuptools
# spack -e . add py-mochi-sonata
# spack -e . concretize
# spack -e . install
