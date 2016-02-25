#!/bin/bash

set -e
set -x

export PYPY_LOCATION
case "${TOXENV}" in
    py26)
        PYPY_LOCATION=""
        ;;
    py33)
        PYPY_LOCATION=""
        ;;
    py34)
        PYPY_LOCATION=""
        ;;
    *)
        PYPY_LOCATION=`python -c "import glob; import os; print os.path.abspath(glob.glob('../pypy-pypy*')[0])"`
        ;;
esac

tox
