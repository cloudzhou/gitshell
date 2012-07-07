from django.db import models
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, queryraw, execute, count, get, get_many
from gitshell.settings import PRIVATE_REPO_PATH, PUBLIC_REPO_PATH, GIT_BARE_REPO_PATH
from gitshell.gsuser.models import UserprofileManager

class Repo(BaseModel):
    user_id = models.IntegerField()
    name = models.CharField(max_length=64)
    desc = models.CharField(max_length=512, default='')
    lang = models.CharField(max_length=16)
    auth_type = models.SmallIntegerField(default=0)
    used_quote = models.BigIntegerField(default=0)

    commit = models.IntegerField(default=0)
    watch = models.IntegerField(default=0)
    fork = models.IntegerField(default=0)
    member = models.IntegerField(default=0)

    def get_abs_repopath(self, user_name):
        parent_path = ""
        if self.auth_type == 0:
            parent_path = PUBLIC_REPO_PATH
        else:
            parent_path = PRIVATE_REPO_PATH
        repopath = '%s/%s/%s.git' % (parent_path, user_name, self.name)
        return repopath

class RepoMember(BaseModel):
    repo_id = models.IntegerField()
    user_id = models.IntegerField()
    permission = models.IntegerField(default=0)

# commit history from git: commit_hash parent_hashes tree_hash author committer committer_date subject
# git log -100 --pretty='%h  %p  %t  %an  %cn  %ct  %s'
class CommitHistory(BaseModel):
    repo_id = models.IntegerField()
    repo_name = models.CharField(max_length=64)
    commit_hash = models.CharField(max_length=12)
    parent_hashes = models.CharField(max_length=24)
    tree_hash = models.CharField(max_length=12)
    committer = models.CharField(max_length=30)
    author = models.CharField(max_length=30)
    author_id = models.IntegerField(default=0)
    committer_date = models.DateTimeField()
    subject = models.CharField(max_length=512)
    #refname = models.CharField(max_length=32)

    @classmethod
    def create(self, repo_id, repo_name, commit_hash, parent_hashes, tree_hash, committer, author, author_id, committer_date, subject):
        return CommitHistory(
            repo_id = repo_id,
            repo_name = repo_name,
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
    user_id = models.IntegerField(default=0)
    watch_repo_id = models.IntegerField(default=0)
    watch_user_id = models.IntegerField(default=0)

class ForkHistory(BaseModel):
    user_id = models.IntegerField(default=0)
    repo_id = models.IntegerField()
    fork_repo_id = models.IntegerField()

class Issues(BaseModel):
    repo_id = models.IntegerField()
    user_id = models.IntegerField()
    subject = models.CharField(max_length=128, default='')
    tracker = models.IntegerField(default=0)
    status = models.IntegerField(default=0) 
    assigned = models.IntegerField(default=0)
    priority = models.IntegerField(default=0)
    category = models.CharField(max_length=16, default='')
    content = models.CharField(max_length=1024, default='')
    comment_count = models.IntegerField(default=0)

class IssuesComment(BaseModel):
    issues_id = models.IntegerField()
    user_id = models.IntegerField()
    vote = models.IntegerField(default=0)
    content = models.CharField(max_length=512, default='') 

class RepoManager():

    @classmethod
    def list_repo_by_userId(self, user_id, offset, row_count):
        repoes = query(Repo, 'repo_repo', user_id, 'repo_l_userId', [user_id, offset, row_count])
        return list(repoes)

    @classmethod
    def get_repo_by_id(self, repo_id):
        return get(Repo, 'repo_repo', repo_id)

    @classmethod
    def get_repo_by_name(self, user_name, repo_name):
        user = UserprofileManager.get_user_by_name(user_name)
        if user is None:
            return None
        return RepoManager.get_repo_by_userId_name(user.id, repo_name)

    @classmethod
    def get_repo_by_userId_name(self, user_id, name):
        repoes = query(Repo, 'repo_repo', user_id, 'repo_s_userId_name', [user_id, name])
        if len(list(repoes)) > 0:
            return repoes[0]
        return None

    @classmethod
    def count_repo_by_userId(self, user_id):
        pass

    @classmethod
    def get_commits_by_ids(self, ids):
        return get_many(CommitHistory, 'repo_commithistory', ids)

    @classmethod
    def list_repomember(self, repo_id):
        repoemembers = query(RepoMember, 'repo_repomember', repo_id, 'repomember_l_repoId', [repo_id])
        return list(repoemembers)

    @classmethod
    def list_issues(self, repo_id, assigned_id, tracker, status, priority, orderby, page):
        offset = page*2
        row_count = 3
        rawsql_id = 'repoissues_l_cons_modify'
        if orderby == 'create_time':
            rawsql_id = 'repoissues_l_cons_create'
        repoissues = query(Issues, 'repo_issues', repo_id, rawsql_id, [repo_id, assigned_id, tracker, status, priority, offset, row_count]) 
        return list(repoissues)

    @classmethod
    def get_issues(self, repo_id, issues_id):
        issues = query(Issues, 'repo_issues', repo_id, 'repoissues_s_id', [repo_id, issues_id])
        if len(list(issues)) > 0:
            return issues[0]
        return None

    @classmethod
    def get_issues_comment(self, comment_id):
        issues_comment = get(IssuesComment, 'repo_issuescomment', comment_id)
        return issues_comment

    @classmethod
    def list_issues_comment(self, issues_id, page):
        offset = page*2
        row_count = 2
        issuesComments = query(IssuesComment, 'repo_issuescomment', issues_id, 'issuescomment_l_issuesId', [issues_id, offset, row_count]) 
        return list(issuesComments)
