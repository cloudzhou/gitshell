#!/usr/bin/python

import os
from subprocess import Popen
from subprocess import PIPE
"""
git ls-tree `cat .git/refs/heads/master` -- githooks/
git log -1 --pretty='%ct  %s' -- githooks/
git show HEAD:README.md
git diff 2497dbb67cb29c0448a3c658ed50255cb4de6419 a2f5ec702e58eb5053fc199c590eac29a2627ad7 --
"""
def repo_ls_tree(user, repo, commit_hash, path):
    popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
    result = popen.communicate()[0]
    pass

def repo_cat_file(user, repo, commit_hash, path):
    popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
    result = popen.communicate()[0]
    pass

def repo_log_file(user, repo, commit_hash, path):
    popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
    result = popen.communicate()[0]
    pass

def repo_diff(user, repo, pre_commit_hash, commit_hash, path):
    popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
    result = popen.communicate()[0]
    pass

def repo_ls_tags(user, repo):
    tags = []
    dirpath = '/opt/tmp/gitshell/.git/refs/tags'
    if os.path.exists(dirpath):
        for tag in os.listdir(dirpath):
            tags.append(tag)
    return tags

def repo_ls_branches(user, repo):
    branches = []
    dirpath = '/opt/tmp/gitshell/.git/refs/heads'
    if os.path.exists(dirpath):
        for branch in os.listdir(dirpath):
            branches.append(branch)
    return branches

""" refs: branch, tag """
def get_commit_hash(user, repo, refs):
    popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
    result = popen.communicate()[0]

if __name__ == '__main__':
    print repo_ls_branches(None, None)
