#!/bin/bash

if [ $# -lt 6 ]; then
    exit 128
fi

pullrequest_repo_path="$1"
source_abs_repopath="$2"
source_remote_name="$3"
dest_abs_repopath="$4"
desc_remote_name="$5"
action="$6"

function prepare {
    if [ ! -e "$pullrequest_repo_path" ]; then
        mkdir "$pullrequest_repo_path"
    fi
    
    if [ ! -e "$pullrequest_repo_path/.git" ]; then
        git init $pullrequest_repo_path
    fi
    
    cd $pullrequest_repo_path

    git ls-remote "$source_remote_name"
    if [ $? != 0 ]; then
        git remote add "$source_remote_name" "file://$source_abs_repopath"
    fi
    git ls-remote "$desc_remote_name"
    if [ $? != 0 ]; then
        git remote add "$desc_remote_name" "file://$dest_abs_repopath"
    fi
    git fetch "$source_remote_name"
    git fetch "$desc_remote_name"
}

merge_result=128
function merge {
    git checkout master
    git show-branch $local_source_refs
    if [ $? == 0 ]; then
        git branch -D $local_source_refs
    fi
    git show-branch $local_desc_refs
    if [ $? == 0 ]; then
        git branch -D $local_desc_refs
    fi
    git branch $local_source_refs $source_remote_name/$source_refs
    git branch $local_desc_refs $desc_remote_name/$desc_refs
    git checkout $local_desc_refs
    echo '----------- starting merge -----------'
    git merge $local_source_refs -m "$pullrequest_commit_message"
    if [ $? == 0 ]; then
        git push $desc_remote_name $local_desc_refs:$desc_refs
        if [ $? == 0 ]; then
            merge_result=0
        fi
    else
        git merge --abort
    fi
    exit $merge_result
}

case "$action" in
  prepare)
    prepare
    ;;
  merge)
    prepare
    echo $#
    if [ $# -lt 9 ]; then
        exit 128
    fi
    source_refs="$7"
    desc_refs="$8"
    pullrequest_commit_message="$9"
    local_source_refs="${source_remote_name}-${source_refs}"
    local_desc_refs="${desc_remote_name}-$desc_refs"
    merge
    ;;
  *)
    exit 128
esac
