# -*- coding: utf-8 -*-  
import time
from django.db import models
from django.core.cache import cache
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, queryraw, execute, count, get, get_many, get_version, get_sqlkey
from gitshell.objectscache.da import get_raw, get_raw_many
from gitshell.settings import REPO_PATH, GIT_BARE_REPO_PATH
from gitshell.gsuser.models import GsuserManager
from gitshell.feed.feed import FeedAction

class Repo(BaseModel):
    user_id = models.IntegerField()
    fork_repo_id = models.IntegerField(default=0)
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

    def get_repo_username(self):
        user = GsuserManager.get_user_by_id(self.user_id)
        if user is not None:
            return user.username
        return ''

    def init_repo_username(self):
        self.username = self.get_repo_username()

    def get_abs_repopath(self, user_name):
        repopath = '%s/%s/%s.git' % (REPO_PATH, user_name, self.name)
        return repopath

    username = ''

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

    # field without database
    committer_email = ''
    author_email = ''

    @classmethod
    def create(self, repo_id, repo_name, commit_hash, parent_hashes, tree_hash, author, committer, committer_date, subject, refname, committer_email, author_email):
        commitHistory = CommitHistory(
            repo_id = repo_id,
            repo_name = repo_name,
            commit_hash = commit_hash,
            parent_hashes = parent_hashes,
            tree_hash = tree_hash,
            author = author,
            committer = committer,
            committer_date = committer_date,
            subject = subject,
            refname = refname
        )
        commitHistory.commit_id = int(commit_hash[0:6], 16)
        commitHistory.committer_email = committer_email
        commitHistory.author_email = author_email 
        return commitHistory

    def get_short_refname(self):
        if '/' in self.refname:
            return self.refname[self.refname.rfind('/')+1:]
        return ''

    def get_repo_username(self):
        repo = RepoManager.get_repo_by_id(self.repo_id)
        return repo.get_repo_username()

class WatchHistory(BaseModel):
    user_id = models.IntegerField(default=0)
    watch_repo_id = models.IntegerField(default=0)
    watch_user_id = models.IntegerField(default=0)

#TODO not using now
class ForkHistory(BaseModel):
    repo_id = models.IntegerField()
    fork_repo_id = models.IntegerField()
    user_id = models.IntegerField(default=0)

class PullRequest(BaseModel):
    pull_user_id = models.IntegerField()
    source_repo_id = models.IntegerField()
    source_refname = models.CharField(max_length=32)
    desc_repo_id = models.IntegerField()
    desc_refname = models.CharField(max_length=32)
    title = models.CharField(max_length=256)
    desc = models.CharField(max_length=2048, default='')
    delete_refs = models.SmallIntegerField(default=0)
    status = models.IntegerField(default=0) 

    @classmethod
    def create(self, pull_user_id, source_repo_id, source_refname, desc_repo_id, desc_refname, title, desc, delete_refs, status):
        pullRequest = PullRequest(
            pull_user_id = pull_user_id,
            source_repo_id = source_repo_id,
            source_refname = source_refname,
            desc_repo_id = desc_repo_id,
            desc_refname = desc_refname,
            title = title,
            desc = desc,
            delete_refs = delete_refs,
            status = status,
        )
        return pullRequest

    pull_user = None
    source_repo = None
    desc_repo = None
    short_title = ''
    short_desc = ''
    status_view = '' 
    status_label = ''

    def fillwith(self):
        self.pull_user = GsuserManager.get_user_by_id(self.pull_user_id)
        self.source_repo = RepoManager.get_repo_by_id(self.source_repo_id)
        self.desc_repo = RepoManager.get_repo_by_id(self.desc_repo_id)
        self.source_repo.init_repo_username()
        self.desc_repo.init_repo_username()
        self.short_title = self.title
        self.short_desc = self.desc
        if len(self.short_title) > 20:
            self.short_title = self.short_title[0:20] + '...'
        if len(self.short_desc) > 20:
            self.short_desc = self.short_desc[0:20] + '...'
        self.status_view = PULL_STATUS.VIEW_MAP[self.status]
        self.status_label = PULL_STATUS.LABEL_MAP[self.status]

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

    # field without database
    username = ''
    reponame = ''

class IssuesComment(BaseModel):
    issues_id = models.IntegerField()
    user_id = models.IntegerField()
    vote = models.IntegerField(default=0)
    content = models.CharField(max_length=512, default='') 

    # field without database
    username = ''
    reponame = ''

class RepoManager():

    @classmethod
    def list_repo_by_userId(self, user_id, offset, row_count):
        repoes = query(Repo, user_id, 'repo_l_userId', [user_id, offset, row_count])
        return repoes

    @classmethod
    def list_unprivate_repo_by_userId(self, user_id, offset, row_count):
        repoes = query(Repo, user_id, 'repo_l_unprivate_userId', [user_id, offset, row_count])
        return repoes

    @classmethod
    def list_repo_by_ids(self, ids):
        return get_many(Repo, ids)

    @classmethod
    def list_rawrepo_by_ids(self, ids):
        return get_raw_many(Repo, ids)

    @classmethod
    def get_repo_by_id(self, repo_id):
        return get(Repo, repo_id)

    @classmethod
    def get_repo_by_forkrepo(self, username, repo):
        user = GsuserManager.get_user_by_name(username)
        if user is None:
            return None
        if repo.user_id == user.id:
            return repo
        repo = query_first(Repo, None, 'repo_s_userId_forkrepoId', [user.id, repo.id])
        return repo

    @classmethod
    def list_parent_repo(self, repo, limit):
        parent_repos = []
        repo.init_repo_username()
        parent_repos.append(repo)
        parent_repo = repo
        for x in range(0, limit):
            if parent_repo.fork_repo_id is None or parent_repo.fork_repo_id == 0:
                break
            parent_repo = RepoManager.get_repo_by_id(parent_repo.fork_repo_id)
            parent_repo.init_repo_username()
            if parent_repo is None:
                break
            parent_repos.append(parent_repo)
        return parent_repos

    @classmethod
    def get_rawrepo_by_id(self, repo_id):
        return get_raw(Repo, repo_id)

    @classmethod
    def get_repo_by_name(self, user_name, repo_name):
        user = GsuserManager.get_user_by_name(user_name)
        if user is None:
            return None
        return RepoManager.get_repo_by_userId_name(user.id, repo_name)

    @classmethod
    def get_repo_by_userId_name(self, user_id, name):
        repoes = query(Repo, user_id, 'repo_s_userId_name', [user_id, name])
        if len(repoes) > 0:
            return repoes[0]
        return None

    @classmethod
    def count_repo_by_userId(self, user_id):
        pass

    @classmethod
    def get_commit_by_id(self, id):
        return get(CommitHistory, id)

    @classmethod
    def get_commits_by_ids(self, ids):
        return get_many(CommitHistory, ids)

    @classmethod
    def list_commits_by_commit_ids(self, repo_id, commit_ids):
        return list(CommitHistory.objects.filter(visibly=0).filter(repo_id=repo_id).filter(commit_id__in=commit_ids))

    @classmethod
    def list_repomember(self, repo_id):
        repoemembers = query(RepoMember, repo_id, 'repomember_l_repoId', [repo_id])
        return repoemembers

    @classmethod
    def get_repo_member(self, repo_id, user_id):
        repoMembers = query(RepoMember, repo_id, 'repomember_s_ruid', [repo_id, user_id])
        if len(repoMembers) > 0:
            return repoMembers[0]
        return None

    @classmethod
    def add_member(self, repo_id, user_name):
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
    def remove_member(self, repo_id, user_name):
        user = GsuserManager.get_user_by_name(user_name)
        if user is None:
            return None
        repoMember = self.get_repo_member(repo_id, user.id)
        if repoMember is not None:
            repoMember.visibly = 1
            repoMember.save()

    @classmethod
    def is_repo_member(self, repo, user):
        if user is None:
            return False
        if user.is_authenticated():
            if repo.user_id == user.id:
                return True
            member = self.get_repo_member(repo.id, user.id)
            if member is not None:
                return True
        return False

    @classmethod
    def list_issues_cons(self, repo_id, assigned_ids, trackers, statuses, priorities, orderby, offset, row_count):
        # diff between multi filter and single filter
        rawsql_id = 'issues.list_issues_cons'
        parameters = [
            ','.join(str(x) for x in assigned_ids),
            ','.join(str(x) for x in trackers),
            ','.join(str(x) for x in statuses),
            ','.join(str(x) for x in priorities),
            orderby, offset, row_count]
        version = get_version(Issues, repo_id)
        sqlkey = get_sqlkey(version, rawsql_id, parameters)
        value = cache.get(sqlkey)
        if value is not None:
            return get_many(Issues, value)
        issues = Issues.objects.filter(visibly=0).filter(repo_id=repo_id).filter(assigned__in=assigned_ids).filter(tracker__in=trackers).filter(status__in=statuses).filter(priority__in=priorities).order_by('-'+orderby)[offset : offset+row_count]
        issues_ids = [x.id for x in issues]
        cache.add(sqlkey, issues_ids)
        return list(issues)

    @classmethod
    def list_issues(self, repo_id, orderby, offset, row_count):
        rawsql_id = 'repoissues_l_cons_modify'
        if orderby == 'create_time':
            rawsql_id = 'repoissues_l_cons_create'
        repoissues = query(Issues, repo_id, rawsql_id, [repo_id, offset, row_count]) 
        return repoissues

    @classmethod
    def list_assigned_issues(self, assigned, orderby, offset, row_count):
        rawsql_id = 'repoissues_l_assigned_modify'
        if orderby == 'create_time':
            rawsql_id = 'repoissues_l_assigned_create'
        repoissues = query(Issues, None, rawsql_id, [assigned, offset, row_count]) 
        return repoissues

    @classmethod
    def get_issues_by_id(self, issues_id):
        return get(Issues, issues_id)

    @classmethod
    def get_issues(self, repo_id, issues_id):
        issues = query(Issues, repo_id, 'repoissues_s_id', [repo_id, issues_id])
        if len(issues) > 0:
            return issues[0]
        return None

    @classmethod
    def get_issues_comment(self, comment_id):
        issues_comment = get(IssuesComment, comment_id)
        return issues_comment

    @classmethod
    def list_issues_comment(self, issues_id, offset, row_count):
        issuesComments = query(IssuesComment, issues_id, 'issuescomment_l_issuesId', [issues_id, offset, row_count]) 
        return issuesComments

    @classmethod
    def list_fork_repo(self, repo_id):
        forkRepos = query(Repo, None, 'repo_l_forkRepoId', [repo_id]) 
        repo_ids = [o.id for o in forkRepos]
        unorder_repos = get_many(Repo, repo_ids)
        repo_map = {}
        for repo in unorder_repos:
            repo_map[repo.id] = repo
        order_repos = [] 
        for repo_id in repo_ids:
            if repo_id in repo_map:
                order_repos.append(repo_map[repo_id])
        return order_repos

    @classmethod
    def list_watch_user(self, repo_id):
        watchHistory = query(WatchHistory, None, 'watchhistory_l_repoId', [repo_id])
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
        if userprofile.id == watch_userprofile.id:
            return False
        if userprofile.watch >= 100:
            return False
        watchHistorys = query(WatchHistory, userprofile.id, 'watchhistory_s_user', [userprofile.id, watch_userprofile.id])
        feedAction = FeedAction()
        timestamp = int(time.time())
        if len(watchHistorys) > 0:
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
        if userprofile.id == watch_userprofile.id:
            return False
        watchHistorys = query(WatchHistory, userprofile.id, 'watchhistory_s_user', [userprofile.id, watch_userprofile.id])
        watchHistory = None
        if len(watchHistorys) > 0:
            watchHistory = watchHistorys[0]
        if watchHistory is not None:
            watchHistory.visibly = 1
            watchHistory.save()
            userprofile.watch = userprofile.watch - 1
            if userprofile.watch < 0:
                userprofile.watch = 0
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
        if watch_repo.auth_type == 2:
            member = self.get_repo_member(watch_repo.id, userprofile.id)
            if member == None:
                return False
        if userprofile.watchrepo >= 100:
            return False
        watchHistorys = query(WatchHistory, userprofile.id, 'watchhistory_s_repo', [userprofile.id, watch_repo.id])
        feedAction = FeedAction()
        timestamp = int(time.time())
        if len(watchHistorys) > 0:
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
        watchHistorys = query(WatchHistory, userprofile.id, 'watchhistory_s_repo', [userprofile.id, watch_repo.id])
        watchHistory = None
        if len(watchHistorys) > 0:
            watchHistory = watchHistorys[0]
        if watchHistory is not None:
            watchHistory.visibly = 1
            watchHistory.save()
            userprofile.watchrepo = userprofile.watchrepo - 1
            if userprofile.watchrepo < 0:
                userprofile.watchrepo = 0
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
    def get_pullRequest_by_id(self, repo_id, pullRequest_id):
        pullRequest = get(PullRequest, pullRequest_id)
        if pullRequest.desc_repo_id == repo_id:
            pullRequest.fillwith()
            return pullRequest
        return None

    @classmethod
    def list_pullRequest_by_descRepoId(self, descRepo_id):
        offset = 0
        row_count = 100
        pullRequests = query(PullRequest, descRepo_id, 'pullrequest_l_descRepoId', [descRepo_id, offset, row_count])
        for pullRequest in pullRequests:
            pullRequest.fillwith()
        return pullRequests

    @classmethod
    def list_pullRequest_by_pullUserId(self, pullUser_id):
        offset = 0
        row_count = 100
        pullRequests = query(PullRequest, None, 'pullrequest_l_pullUserId', [pullUser_id, offset, row_count])
        for pullRequest in pullRequests:
            pullRequest.fillwith()
        return pullRequests

    # ====================
    @classmethod
    def merge_repo_map(self, repo_ids):
        repos = self.list_repo_by_ids(repo_ids)
        return self.__inner_merge_repo_map(repos)

    @classmethod
    def merge_repo_map_ignore_visibly(self, repo_ids):
        repos = self.list_rawrepo_by_ids(repo_ids)
        return self.__inner_merge_repo_map(repos)

    @classmethod
    def __inner_merge_repo_map(self, repos):
        repo_vo_dict = {}
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
            repo_vo['auth_type'] = repo.auth_type
            repo_vo['status'] = repo.status
            repo_vo['visibly'] = repo.visibly
            repo_vo_dict[repo.id] = repo_vo
        return repo_vo_dict

class PULL_STATUS:

    NEW = 0
    MERGED = 1
    REJECTED = 2
    CLOSE = 3

    VIEW_MAP = {
        0 : '未合并',
        1 : '合并',
        2 : '拒绝',
        3 : '关闭',
        4 : '合并失败',
    }

    LABEL_MAP = {
        0 : 'label-info',
        1 : 'label-success',
        2 : 'label-inverse',
        3 : 'label-default',
    }
