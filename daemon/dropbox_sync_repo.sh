#!/bin/bash

. /lib/lsb/init-functions
DIR="$( cd "$( dirname "$0" )" && pwd )"

if [ $# -lt 5 ] || [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ]; then
    exit 128
fi

LOCAL_REPO_PATH="/home/git/Repositories"
DROPBOX_REPO_PATH="/home/git/Dropbox/Apps/gitshell/repositories"
SERVER_REPO_PATH="/opt/repo/set"
for path in "$LOCAL_REPO_PATH" "$DROPBOX_REPO_PATH"; do
    if [ ! -e "$path" ]; then
        mkdir -p "$path"
    fi
done

id="$1"
username="$2"
reponame="$3"
dropbox_sync="$4"
visibly="$5"
remote_raw_repo_path="$SERVER_REPO_PATH/${username}/${reponame}.git"
local_sync_repo_path="$LOCAL_REPO_PATH/$id.git"
dropbox_sync_repo_path="$DROPBOX_REPO_PATH/${username}/${id}_${reponame}.git"

# function git clone bare from remote to specail path
function git_clone_bare {
    if [ -z "$1" ]; then
        exit 128
    fi
    sync_repo_path="$1"
    sync_repo_dirpath=`dirname $sync_repo_path`
    if [ ! -e "$sync_repo_dirpath" ]; then
        mkdir -p "$sync_repo_dirpath" 
    fi
    
    if [ ! -e "$sync_repo_path" ]; then
        git clone --bare "ssh://git@gitshell.com:2222/$remote_raw_repo_path" "$sync_repo_path"
    else
        cd "$sync_repo_path"; git fetch; cd -
    fi
}

# 1 rsync to local as backup
git_clone_bare "$local_sync_repo_path"
# 2 delete repo if dropbox_sync == 0 or visibly == 1
if [ "$dropbox_sync" == '0' ] || [ "$visibly" == '1' ]; then
    if [ -e "$dropbox_sync_repo_path" ]; then
        rm -rf "$dropbox_sync_repo_path"
        exit 0
    fi
fi
# 3 rsync repo to dropbox
git_clone_bare "$dropbox_sync_repo_path"





