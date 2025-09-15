#!/bin/bash

set -eux pipefail

env

ls -halF $RUN_DIR

pushd /Downloads
git clone https://github.com/dakotablair/ChimbukoVisualizationII.git

pushd ChimbukoVisualizationII
git checkout actions_unstable

mkdir -p data/grid
ln -s /Downloads/repeat_1rank data/grid/
popd

pushd /opt/spack-environment/ && \
    source /spack/spack/share/spack/setup-env.sh && \
    spack env activate .
popd

# python -m pip install -r requirements.large.txt
# python -m pip install -r requirements.txt

popd

CHIMBUKO_VIZ_ROOT=/Downloads/ChimbukoVisualizationII ./run.sh

set +ex
