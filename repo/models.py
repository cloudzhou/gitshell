# -*- coding: utf-8 -*-  
import time
from django.db import models
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, queryraw, execute, count, get, get_many
from gitshell.settings import PRIVATE_REPO_PATH, PUBLIC_REPO_PATH, GIT_BARE_REPO_PATH
from gitshell.gsuser.models import GsuserManager
from gitshell.feed.feed import FeedAction

class Repo(BaseModel):
    user_id = models.IntegerField()
    fork_repo_id = models.IntegerField()
    name = models.CharField(max_length=64)
    desc = models.CharField(max_length=512, default='')
    lang = models.CharField(max_length=16)
    auth_type = models.SmallIntegerField(default=0)
    used_quote = models.BigIntegerField(default=0)

    commit = models.IntegerField(default=0)
    watch = models.IntegerField(default=0)
    fork = models.IntegerField(default=0)
    member = models.IntegerField(default=0)

    status = models.IntegerField(default=0) 

    @classmethod
    def create(self, user_id, fork_repo_id, name, desc, lang, auth_type, used_quote):
        repo = Repo(
            user_id = user_id,
            fork_repo_id = fork_repo_id,
            name = name,
            desc = desc,
            lang = lang,
            auth_type = auth_type,
            used_quote = used_quote,
        )
        return repo

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
    commit_id = models.IntegerField()
    commit_hash = models.CharField(max_length=12)
    parent_hashes = models.CharField(max_length=24)
    tree_hash = models.CharField(max_length=12)
    committer = models.CharField(max_length=30)
    author = models.CharField(max_length=30)
    committer_date = models.DateTimeField()
    subject = models.CharField(max_length=512)
    refname = models.CharField(max_length=32)

    @classmethod
    def create(self, repo_id, repo_name, commit_hash, parent_hashes, tree_hash, committer, author, committer_date, subject, refname):
        commitHistory = CommitHistory(
            repo_id = repo_id,
            repo_name = repo_name,
            commit_hash = commit_hash,
            parent_hashes = parent_hashes,
            tree_hash = tree_hash,
            committer = committer,
            author = author,
            committer_date = committer_date,
            subject = subject,
            refname = refname
        )
        commitHistory.commit_id = int(commit_hash[0:7], 16)
        return commitHistory

class WatchHistory(BaseModel):
    user_id = models.IntegerField(default=0)
    watch_repo_id = models.IntegerField(default=0)
    watch_user_id = models.IntegerField(default=0)

class ForkHistory(BaseModel):
    repo_id = models.IntegerField()
    fork_repo_id = models.IntegerField()
    user_id = models.IntegerField(default=0)

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
    def list_repo_by_ids(self, ids):
        return get_many(Repo, 'repo_repo', ids)

    @classmethod
    def get_repo_by_id(self, repo_id):
        return get(Repo, 'repo_repo', repo_id)

    @classmethod
    def get_repo_by_name(self, user_name, repo_name):
        user = GsuserManager.get_user_by_name(user_name)
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
    def get_repo_member(self, repo_id, user_id):
        repoMembers = query(RepoMember, 'repo_repomember', repo_id, 'repomember_s_ruid', [repo_id, user_id])
        if len(list(repoMembers)) > 0:
            return repoMembers[0]
        return None

    @classmethod
    def add_member(self, repo_id, username):
        user = GsuserManager.get_user_by_name(user_name)
        if user is None:
            return None
        repoMember = self.get_repo_member(repo_id, user.id)
        if repoMember is None:
            repoMember = RepoMember()
            repoMember.repo_id = repo_id
            repoMember.user_id = user.id
            repoMember.save()

    @classmethod
    def remove_member(self, repo_id, username):
        user = GsuserManager.get_user_by_name(user_name)
        if user is None:
            return None
        repoMember = self.get_repo_member(repo_id, user.id)
        if repoMember is not None:
            repoMember.visibly = 1
            repoMember.save()

    @classmethod
    def list_issues_cons(self, repo_id, assigned_ids, trackers, statuses, priorities, orderby, page):
        offset = page*2
        row_count = 3
        # diff between multi filter and single filter
        issues = Issues.objects.filter(visibly=0).filter(assigned__in=assigned_ids).filter(tracker__in=trackers).filter(status__in=statuses).filter(priority__in=priorities).order_by('-'+orderby)[offset : offset+row_count]
        return list(issues)

    @classmethod
    def list_issues(self, repo_id, orderby, page):
        offset = page*2
        row_count = 3
        rawsql_id = 'repoissues_l_cons_modify'
        if orderby == 'create_time':
            rawsql_id = 'repoissues_l_cons_create'
        repoissues = query(Issues, 'repo_issues', repo_id, rawsql_id, [repo_id, offset, row_count]) 
        return list(repoissues)

    @classmethod
    def list_assigned_issues(self, assigned, orderby, page):
        offset = page*2
        row_count = 3
        rawsql_id = 'repoissues_l_assigned_modify'
        if orderby == 'create_time':
            rawsql_id = 'repoissues_l_assigned_create'
        repoissues = query(Issues, 'repo_issues', None, rawsql_id, [assigned, offset, row_count]) 
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

    @classmethod
    def list_fork_repo(self, repo_id):
        forkHistorys = query(ForkHistory, 'repo_forkhistory', repo_id, 'forkhistory_l_repoId', [repo_id]) 
        repo_ids = [o.fork_repo_id for o in forkHistorys]
        unorder_repos = get_many(Repo, 'repo_repo', repo_ids)
        repo_map = {}
        for repo in unorder_repos:
            repo_map[repo.id] = repo
        order_repos = [] 
        for repo_id in repo_ids:
            if repo_id in repo_map:
                order_repos.append(repo_map[repo_id])
        return order_repos

    #TODO about pk
    @classmethod
    def list_watch_user(self, repo_id):
        watchHistory = query(WatchHistory, 'repo_watchhistory', repo_id, 'watchhistory_l_repoId', [repo_id])
        user_ids = [o.user_id for o in watchHistory]
        user_map = GsuserManager.map_users(user_ids)
        watch_user = []
        for user_id in user_ids:
            if user_id in user_map:
                watch_user.append(user_map[user_id])
        return watch_user

    @classmethod
    def is_watched_user(self, user_id, watch_user_id):
        feedAction = FeedAction()
        return feedAction.is_watch_user(user_id, watch_user_id)

    @classmethod
    def is_watched_repo(self, user_id, watch_repo_id):
        feedAction = FeedAction()
        return feedAction.is_watch_repo(user_id, watch_repo_id)

    @classmethod
    def watch_user(self, userprofile, watch_userprofile):
        if userprofile.watch >= 100:
            return False
        watchHistorys = query(WatchHistory, 'repo_watchhistory', userprofile.id, 'watchhistory_s_user', [userprofile.id, watch_userprofile.id])
        feedAction = FeedAction()
        timestamp = int(time.time())
        if len(list(watchHistorys)) > 0:
            # redis action
            feedAction.add_watch_user(userprofile.id, timestamp, watch_userprofile.id)
            feedAction.add_bewatch_user(watch_userprofile.id, timestamp, userprofile.id)
            return True
        watchHistory = WatchHistory()
        watchHistory.user_id = userprofile.id
        watchHistory.watch_user_id = watch_userprofile.id
        watchHistory.save()
        userprofile.watch = userprofile.watch + 1
        userprofile.save()
        watch_userprofile.be_watched = watch_userprofile.be_watched + 1
        watch_userprofile.save()
        # redis action
        feedAction.add_watch_user(userprofile.id, timestamp, watch_userprofile.id)
        feedAction.add_bewatch_user(watch_userprofile.id, timestamp, userprofile.id)
        return True

    @classmethod
    def unwatch_user(self, userprofile, watch_userprofile):
        watchHistorys = query(WatchHistory, 'repo_watchhistory', userprofile.id, 'watchhistory_s_user', [userprofile.id, watch_userprofile.id])
        watchHistory = None
        if len(list(watchHistorys)) > 0:
            watchHistory = watchHistorys[0]
        if watchHistory is not None:
            watchHistory.visibly = 1
            watchHistory.save()
            userprofile.watch = userprofile.watch - 1
            userprofile.save()
            watch_userprofile.be_watched = watch_userprofile.be_watched - 1
            if watch_userprofile.be_watched < 0:
                watch_userprofile.be_watched = 0
            watch_userprofile.save()
        # redis action
        feedAction = FeedAction()
        feedAction.remove_watch_user(userprofile.id, watch_userprofile.id)
        feedAction.remove_bewatch_user(watch_userprofile.id, userprofile.id)
        return True

    @classmethod
    def watch_repo(self, userprofile, watch_repo):
        if userprofile.watchrepo >= 100:
            return False
        watchHistorys = query(WatchHistory, 'repo_watchhistory', userprofile.id, 'watchhistory_s_repo', [userprofile.id, watch_repo.id])
        feedAction = FeedAction()
        timestamp = int(time.time())
        if len(list(watchHistorys)) > 0:
            # redis action
            feedAction.add_watch_repo(userprofile.id, timestamp, watch_repo.id)
            return True
        watchHistory = WatchHistory()
        watchHistory.user_id = userprofile.id
        watchHistory.watch_repo_id = watch_repo.id
        watchHistory.save()
        userprofile.watchrepo = userprofile.watchrepo + 1
        userprofile.save()
        watch_repo.watch = watch_repo.watch + 1
        watch_repo.save()
        # redis action
        feedAction.add_watch_repo(userprofile.id, timestamp, watch_repo.id)
        return True

    @classmethod
    def unwatch_repo(self, userprofile, watch_repo):
        watchHistorys = query(WatchHistory, 'repo_watchhistory', userprofile.id, 'watchhistory_s_repo', [userprofile.id, watch_repo.id])
        watchHistory = None
        if len(list(watchHistorys)) > 0:
            watchHistory = watchHistorys[0]
        if watchHistory is not None:
            watchHistory.visibly = 1
            watchHistory.save()
            userprofile.watchrepo = userprofile.watchrepo - 1
            userprofile.save()
            watch_repo.watch = watch_repo.watch - 1
            if watch_repo.watch < 0:
                watch_repo.watch = 0
            watch_repo.save()
        # redis action
        feedAction = FeedAction()
        feedAction.remove_watch_repo(userprofile.id, watch_repo.id)
        return True

    @classmethod
    def merge_repo_map(self, repo_ids):
        repo_vo_dict = {}
        repos = self.list_repo_by_ids(repo_ids)
        user_ids = [x.user_id for x in repos]
        users = GsuserManager.list_user_by_ids(user_ids)
        users_map = dict([(x.id, x) for x in users])
        for repo in repos:
            repo_vo = {}
            repo_vo['id'] = repo.id
            if repo.user_id in users_map:
                repo_vo['username'] = users_map[repo.user_id].username
            repo_vo['name'] = repo.name
            repo_vo['desc'] = repo.desc
            repo_vo['create_time'] = time.mktime(repo.create_time.timetuple())
            repo_vo['modify_time'] = time.mktime(repo.modify_time.timetuple())
            repo_vo_dict[repo.id] = repo_vo
        return repo_vo_dict
