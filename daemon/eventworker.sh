#!/bin/bash

DIR="$( cd "$( dirname "$0" )" && pwd )"
cd $DIR; cd ../../
GITSHELL_DIR=`pwd`

export PYTHONPATH=$GITSHELL_DIR
export DJANGO_SETTINGS_MODULE=gitshell.settings
python "$GITSHELL_DIR/gitshell/daemon/eventworker.py"
