#!/usr/bin/python

"""
git ls-tree `cat .git/refs/heads/master` -- githooks/
git log -1 --pretty='%ct  %s' -- githooks/
git diff 2497dbb67cb29c0448a3c658ed50255cb4de6419 a2f5ec702e58eb5053fc199c590eac29a2627ad7 --
"""
def repo_ls_tree(repo, path):
    pass

def repo_cat_file(repo, path):
    pass

def repo_log_file(repo, path):
    pass

def repo_diff(repo, pre_commit_hash, commit_hash, path):
    pass
