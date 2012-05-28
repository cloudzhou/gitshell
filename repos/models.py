from django.db import models
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, queryraw, execute, count

class Repos(BaseModel):
    user_id = models.IntegerField()
    name = models.CharField(max_length=64)
    desc = models.CharField(max_length=512, default='')
    lang = models.CharField(max_length=16)
    auth_type = models.SmallIntegerField(default=0)
    quote = models.BigIntegerField(default=0)

    commit = models.IntegerField(default=0)
    watch = models.IntegerField(default=0)
    fork = models.IntegerField(default=0)
    member = models.IntegerField(default=0)

class ReposMember(BaseModel):
    repos_id = models.IntegerField()
    user_id = models.IntegerField()
    permission = models.SmallIntegerField(default=0)

# commit history from git: commit_hash parent_hashes tree_hash committer author committer_date subject
# git log -100 --pretty='%h  %p  %t  %an  %cn  %ct  %s'
class CommitHistory(BaseModel):
    repos_id = models.IntegerField()
    commit_hash = models.CharField(max_length=12)
    parent_hashes = models.CharField(max_length=24)
    tree_hash = models.CharField(max_length=12)
    committer = models.CharField(max_length=30)
    author = models.CharField(max_length=30)
    author_id = models.IntegerField()
    committer_date = models.DateTimeField()
    subject = models.CharField(max_length=512)
    #refname = models.CharField(max_length=32)

    @classmethod
    def create(self, repos_id, commit_hash, parent_hashes, tree_hash, committer, author, author_id, committer_date, subject):
        return CommitHistory(
            repos_id = repos_id,
            commit_hash = commit_hash,
            parent_hashes = parent_hashes,
            tree_hash = tree_hash,
            committer = committer,
            author = author,
            author_id = author_id,
            committer_date = committer_date,
            subject = subject
        )

class WatchHistory(BaseModel):
    repos_id = models.IntegerField()
    user_id = models.IntegerField()

class ForkHistory(BaseModel):
    repos_id = models.IntegerField()
    fork_repos_id = models.IntegerField()

class ReposManager():

    @classmethod
    def list_repos_by_userId(self, user_id, offset, row_count):
        reposes = query(Repos, 'repos_repos', user_id, 'repos_l_userId', [user_id, offset, row_count])
        return list(reposes)

    @classmethod
    def get_repos_by_userId_id(self, user_id, rid):
        pass

    @classmethod
    def get_repos_by_userId_name(self, user_id, name):
        reposes = query(Repos, 'repos_repos', user_id, 'repos_s_userId_name', [user_id, name])
        if len(list(reposes)) > 0:
            return reposes[0]
        return None

    @classmethod
    def count_repos_by_userId(self, user_id):
        pass

