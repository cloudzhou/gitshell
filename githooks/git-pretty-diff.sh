#!/bin/bash

set -e
cd $1
if [ "$2" == '0000000000000000000000000000000000000000' ]; then
    git diff --stat $3
    echo '-----------------------'
    git diff $3
else
    git diff --stat $2..$3
    echo '-----------------------'
    git diff $2..$3
fi
