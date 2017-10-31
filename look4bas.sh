#!/bin/bash
_thisdir=`dirname ${BASH_SOURCE[0]}`
export PYTHONPATH="$PYTHONPATH:$_thisdir"
python3 -m look4bas
