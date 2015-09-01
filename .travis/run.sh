#!/bin/bash

set -e
set -x

case "${TOX_ENV}" in
    py26)
        expoert PYPY_LOCATION=""
        ;;
    py33)
        export PYPY_LOCATION=""
        ;;
    py34)
        export PYPY_LOCATION=""
        ;;
    *)
        export PYPY_LOCATION=`python -c "import glob; import os; print os.path.abspath(glob.glob('../pypy-pypy*')[0])"`
        ;;
esac

tox -e $TOX_ENV
