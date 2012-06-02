#!/bin/bash

cd $1
if [ "$2" == '0000000000000000000000000000000000000000' ]; then
    git log -100 --pretty='%h  %p  %t  %an  %cn  %ct  %s' $3
else
    git log -100 --pretty='%h  %p  %t  %an  %cn  %ct  %s' $2..$3
fi
