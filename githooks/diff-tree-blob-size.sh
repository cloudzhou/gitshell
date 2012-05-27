#!/bin/bash

if [ $# -lt 4 ]; then
    exit 1
fi

args=("$@")
# abspath is the hooks path
abspath=${args[0]}
# private and public move
if [ ! -e $abspath ]; then
    private=`echo $abspath | egrep -c '^/opt/repos/private/'`
    if [ $private -gt 0 ]; then
        abspath=`echo $abspath | sed 's:^/opt/repos/private/:/opt/repos/public/:'`
    else
        abspath=`echo $abspath | sed 's:^/opt/repos/public/:/opt/repos/private/:'`
    fi
    if [ ! -e $abspath ]; then
        return 0
    fi
fi
cd $abspath && cd ..

index=1
size=0
du_size=0
tempfile=`mktemp`

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
    /usr/bin/git diff-tree --raw -r -c -M -C --no-commit-id $oldrev $newrev |\
    head -n 100 |\
    awk '{print $4}' > $tempfile
    total_line=`cat $tempfile|wc -l`
    if [ $total_line -ge 100 ]; then
        du_size=`du -sb .`
        break
    fi
    refsize=`/usr/bin/git cat-file --batch-check < $tempfile | awk 'BEGIN{count=0}{count+=$3}END{print count}'`
    let size=($size+$refsize)
done
    
rm $tempfile

if [ $du_size -eq 0 ]; then
    echo "+$size"
else
    echo "$du_size"
fi
