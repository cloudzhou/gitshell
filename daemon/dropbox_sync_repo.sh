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
        git clone --bare --mirror "ssh://git@gitshell.com:2222/$remote_raw_repo_path" "$sync_repo_path"
        cd "$sync_repo_path"; git update-server-info; cd -
    else
        cd "$sync_repo_path"; git fetch; git update-server-info; cd -
    fi
}

# 1 sync to local as backup
if [ "$visibly" == '0' ]; then
    git_clone_bare "$local_sync_repo_path"
fi

# 2 sync to dropbox
if [ "$visibly" == '0' ] && [ "$dropbox_sync" == '1' ]; then
    # sync repo to dropbox
    git_clone_bare "$dropbox_sync_repo_path"
else
    # delete repo if visibly == 1 or dropbox_sync == 0
    if [ -e "$dropbox_sync_repo_path" ]; then
        rm -rf "$dropbox_sync_repo_path"
    fi
fi





