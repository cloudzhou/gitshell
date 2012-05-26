#!/bin/bash

if [ $# -lt 4 ]; then
    exit 1
fi

args=("$@")
abspath=${args[0]}
# private and public move
if [ ! -e $abspath ]
    return 0
fi
cd $abspath

index=1
while [ $index -lt $# ]; do
    oldrev=${args[$index]}
    let index=($index+1)
    newrev=${args[$index]}
    let index=($index+1)
    refname=${args[$index]}
    let index=($index+1)
    if [ -z "$oldrev" ] || [ -z "$newrev" ] || [ -z "$refname" ]; then
        continue
    fi
    tempfile=`mktemp`
    /usr/bin/git diff-tree --raw -r -c -M -C --no-commit-id $oldrev $newrev |\
    head -n 100 |\
    awk '{print $4}' > $tempfile
    count=`/usr/bin/git cat-file --batch-check < $tempfile | awk 'BEGIN{count=0}{count+=$3}END{print count}'`
    rm $tempfile
    echo "+$count"
done
