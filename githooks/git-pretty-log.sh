#!/bin/bash

cd $1
cd ..
git log -100 --pretty='%h  %p  %t  %an  %cn  %ct  %s' $2..$3
