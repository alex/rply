#!/bin/bash

set -e
set -x

export PYPY_LOCATION
case "${TOXENV}" in
    py3*)
        PYPY_LOCATION=""
        ;;
    *)
        PYPY_LOCATION=$(python -c "import glob; import os; print os.path.abspath(glob.glob('../pypy-*')[0])")
        ;;
esac

tox
