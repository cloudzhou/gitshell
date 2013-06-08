#!/bin/bash

set -e
ulimit -f 327680 ; ulimit -m 1048576 ; ulimit -v 1048576

local_repo_path="$1"
remote_git_url="$2"

/usr/bin/git clone -q --bare "$remote_git_url" "$local_repo_path"
if [ $? == 0 ]; then
    rm "$local_repo_path/hooks/"*
    cp /opt/repo/gitbare/hooks/* "$local_repo_path/hooks/"
    chmod +x "$local_repo_path/hooks/"*
    cd "$local_repo_path"
    /usr/bin/git update-server-info
    dusb=`du -sb $local_repo_path | awk '{print $1}'`
    echo -n "$dusb"
    exit 0
fi
echo -n "0"
exit 128
