#!/bin/bash

cd $1
git log -100 --pretty='%h  %p  %t  %an  %cn  %ct  %s' $2..$3
