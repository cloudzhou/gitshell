#!/bin/bash

DIR="$( cd "$( dirname "$0" )" && pwd )"
cd $DIR; cd ../../
GITSHELL_DIR=`pwd`

export PYTHONPATH=$GITSHELL_DIR
export DJANGO_SETTINGS_MODULE=gitshell.settings

. /lib/lsb/init-functions

SCRIPT="$GITSHELL_DIR/gitshell/daemon/importrepoworker.py"
LOG_PATH="/opt/run/var/log"
current=`date +"%s"`
LOG_FILENAME="$LOG_PATH/importrepo.$current.log"
case "$1" in
  start)
    python "$SCRIPT" start  > $LOG_FILENAME 2 >& 1 &
    ;;
  stop)
    python "$SCRIPT" stop
    ;;
  *)
    log_action_msg "Usage: ${SCRIPT} {start|stop}"
    exit 1
esac
