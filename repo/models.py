# -*- coding: utf-8 -*-  
import os, time, re
from django.db import models
from django.core.cache import cache
from gitshell.objectscache.models import BaseModel, CacheKey
from gitshell.objectscache.da import query, query_first, queryraw, execute, count, get, get_many, get_version, get_sqlkey, get_raw, get_raw_many
from gitshell.settings import REPO_PATH, GIT_BARE_REPO_PATH
from gitshell.gsuser.models import GsuserManager
from gitshell.feed.feed import FeedAction
from gitshell.gsuser.middleware import KEEP_REPO_NAME

class Repo(BaseModel):
    user_id = models.IntegerField()
    fork_repo_id = models.IntegerField(default=0)
    username = models.CharField(max_length=64)
    name = models.CharField(max_length=64)
    desc = models.CharField(max_length=512, default='')
    lang = models.CharField(max_length=16)
    auth_type = models.SmallIntegerField(default=0)
    used_quote = models.BigIntegerField(default=0)

    commit = models.IntegerField(default=0)
    watch = models.IntegerField(default=0)
    star = models.IntegerField(default=0)
    fork = models.IntegerField(default=0)
    member = models.IntegerField(default=0)

    deploy_url = models.CharField(max_length=40, null=True)
    dropbox_sync = models.IntegerField(default=0)
    dropbox_url = models.CharField(max_length=64, null=True)
    last_push_time = models.DateTimeField(auto_now=True, null=True)

    status = models.IntegerField(default=0) 

    @classmethod
    def create(self, user_id, fork_repo_id, username, name, desc, lang, auth_type, used_quote):
        repo = Repo(
            user_id = user_id,
            fork_repo_id = fork_repo_id,
            username = username,
            name = name,
            desc = desc,
            lang = lang,
            auth_type = auth_type,
            used_quote = used_quote,
        )
        return repo

    def get_relative_repopath(self):
        relative_repopath = '%s/%s.git' % (self.username, self.name)
        return relative_repopath

    def get_abs_repopath(self):
        abs_repopath = '%s/%s/%s.git' % (REPO_PATH, self.username, self.name)
        return abs_repopath

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
        return repo.username

class Star(BaseModel):
    user_id = models.IntegerField(default=0)
    star_repo_id = models.IntegerField(default=0)
    star_user_id = models.IntegerField(default=0)

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
    merge_user_id = models.IntegerField()
    source_user_id = models.IntegerField()
    source_repo_id = models.IntegerField()
    source_refname = models.CharField(max_length=32)
    desc_user_id = models.IntegerField()
    desc_repo_id = models.IntegerField()
    desc_refname = models.CharField(max_length=32)
    title = models.CharField(max_length=256)
    desc = models.CharField(max_length=2048, default='')
    delete_refs = models.SmallIntegerField(default=0)
    status = models.IntegerField(default=0) 

    @classmethod
    def create(self, pull_user_id, merge_user_id, source_user_id, source_repo_id, source_refname, desc_user_id, desc_repo_id, desc_refname, title, desc, delete_refs, status):
        pullRequest = PullRequest(
            pull_user_id = pull_user_id,
            merge_user_id = merge_user_id,
            source_user_id = source_user_id,
            source_repo_id = source_repo_id,
            source_refname = source_refname,
            desc_user_id = desc_user_id,
            desc_repo_id = desc_repo_id,
            desc_refname = desc_refname,
            title = title,
            desc = desc,
            delete_refs = delete_refs,
            status = status,
        )
        return pullRequest

    pull_user = None
    merge_user = None
    source_repo = None
    desc_repo = None
    short_title = ''
    short_desc = ''
    status_view = '' 
    status_label = ''

    def fillwith(self):
        self.pull_user = GsuserManager.get_user_by_id(self.pull_user_id)
        self.merge_user = GsuserManager.get_user_by_id(self.merge_user_id)
        self.source_repo = RepoManager.get_repo_by_id(self.source_repo_id)
        self.desc_repo = RepoManager.get_repo_by_id(self.desc_repo_id)
        self.short_title = self.title
        self.short_desc = self.desc
        if len(self.short_title) > 20:
            self.short_title = self.short_title[0:20] + '...'
        if len(self.short_desc) > 20:
            self.short_desc = self.short_desc[0:20] + '...'
        self.status_view = PULL_STATUS.VIEW_MAP[self.status]
        self.status_label = PULL_STATUS.LABEL_MAP[self.status]

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
    def list_repo_by_last_push_time(self, last_push_time):
        return query(Repo, None, 'repo_l_last_push_time', [last_push_time])

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
        child_repo = self.get_childrepo_by_user_forkrepo(user, repo)
        if child_repo is not None:
            return child_repo
        if repo.fork_repo_id is None:
            return None
        parent_repo = RepoManager.get_repo_by_id(repo.fork_repo_id)
        if parent_repo is None:
            return None
        if parent_repo.user_id == user.id:
            return parent_repo

    @classmethod
    def get_childrepo_by_user_forkrepo(self, user, repo):
        child_repo = query_first(Repo, None, 'repo_s_userId_forkrepoId', [user.id, repo.id])
        return child_repo

    @classmethod
    def list_parent_repo(self, repo, limit):
        parent_repos = []
        parent_repos.append(repo)
        parent_repo = repo
        for x in range(0, limit):
            if parent_repo.fork_repo_id is None or parent_repo.fork_repo_id == 0:
                break
            parent_repo = RepoManager.get_repo_by_id(parent_repo.fork_repo_id)
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
        _count = count(Repo, None, 'repo_c_userId', [user_id])
        return _count

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
    def list_star_repo(self, user_id, offset, row_count):
        stars = query(Star, user_id, 'star_l_userId', [user_id, offset, row_count])
        repos = []
        for x in stars:
            repo = RepoManager.get_repo_by_id(x.star_repo_id)
            if repo is None or repo.visibly == 1:
                x.visibly = 1
                x.save()
                continue
            repos.append(repo)
        return repos

    @classmethod
    def list_star_user(self, repo_id, offset, row_count):
        stars = query(Star, None, 'star_l_repoId', [repo_id, offset, row_count])
        userprofiles = []
        for x in stars:
            user = GsuserManager.get_user_by_id(x.user_id)
            userprofile = GsuserManager.get_userprofile_by_id(x.user_id)
            if userprofile is None or userprofile.visibly == 1:
                x.visibly = 1
                x.save()
                continue
            userprofile.date_joined = time.mktime(user.date_joined.timetuple())
            userprofile.last_login = time.mktime(user.last_login.timetuple())
            userprofiles.append(userprofile)
        return userprofiles

    @classmethod
    def is_stared_repo(self, user_id, repo_id):
        repo = RepoManager.get_repo_by_id(repo_id)
        if repo is None:
            return False
        star = query_first(Star, user_id, 'star_s_repo', [user_id, repo_id])
        return star is not None

    @classmethod
    def star_repo(self, user_id, repo_id):
        repo = RepoManager.get_repo_by_id(repo_id)
        if repo is None:
            return False
        star = query_first(Star, user_id, 'star_s_repo', [user_id, repo_id])
        if star is None:
            star = Star()
            star.user_id = user_id
            star.star_user_id = 0
            star.star_repo_id = repo_id
            star.save()
            repo.star = repo.star + 1
            repo.save()
        return True

    @classmethod
    def unstar_repo(self, user_id, repo_id):
        repo = RepoManager.get_repo_by_id(repo_id)
        if repo is None:
            return False
        star = query_first(Star, user_id, 'star_s_repo', [user_id, repo_id])
        if star is not None:
            star.visibly = 1
            star.save()
            repo.star = repo.star - 1
            if repo.star < 0:
                repo.star = 0
            repo.save()
        return True

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
    def watch_repo(self, user, userprofile, watch_repo):
        if watch_repo.auth_type == 2:
            if not self.is_repo_member(watch_repo, user):
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
    def unwatch_repo(self, user, userprofile, watch_repo):
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
    def get_pullRequest_by_id(self, id):
        pullRequest = get(PullRequest, id)
        if pullRequest is not None:
            pullRequest.fillwith()
        return pullRequest

    @classmethod
    def get_pullRequest_by_repoId_id(self, repo_id, pullRequest_id):
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

    @classmethod
    def list_pullRequest_by_mergeUserId(self, mergeUser_id):
        offset = 0
        row_count = 100
        pullRequests = query(PullRequest, None, 'pullrequest_l_mergeUserId', [mergeUser_id, offset, row_count])
        for pullRequest in pullRequests:
            pullRequest.fillwith()
        return pullRequests

    @classmethod
    def count_pullRequest_by_descRepoId(self, descRepo_id, status):
        _count = count(PullRequest, descRepo_id, 'pullrequest_c_descRepoId', [descRepo_id, status])
        return _count

    @classmethod
    def count_pullRequest_by_mergeUserId(self, mergeUser_id, status):
        _count = count(PullRequest, None, 'pullrequest_c_mergeUserId', [mergeUser_id, status])
        return _count

    @classmethod
    def delete_repo_commit_version(self, repo):
        cache.delete(CacheKey.REPO_COMMIT_VERSION % repo.id)

    @classmethod
    def check_export_ok_file(self, repo):
        if repo is None:
            return
        auth_type = repo.auth_type
        repo_path = repo.get_abs_repopath()
        git_daemon_export_ok_file_path = '%s/%s' % (repo_path, 'git-daemon-export-ok')
        if auth_type == 0:
            if os.path.exists(repo_path) and not os.path.exists(git_daemon_export_ok_file_path):
                with open(git_daemon_export_ok_file_path, 'w') as _file:
                    _file.close()
        else:
            if os.path.exists(repo_path) and os.path.exists(git_daemon_export_ok_file_path):
                os.remove(git_daemon_export_ok_file_path)

    @classmethod
    def update_user_repo_quote(self, user, repo, diff_size):
        userprofile = GsuserManager.get_userprofile_by_id(user.id)
        userprofile.used_quote = userprofile.used_quote + diff_size
        repo.used_quote = repo.used_quote + diff_size
        if userprofile.used_quote < 0:
            userprofile.used_quote = 0
        if repo.used_quote < 0:
            repo.used_quote = 0
        userprofile.save()
        repo.save()

    @classmethod
    def is_allowed_reponame_pattern(self, name):
        if name is None or name == '' or len(name) > 1024:
            return False
        if re.match('^[a-zA-Z0-9_\-]+$', name) and not name.startswith('-') and name not in KEEP_REPO_NAME:
            return True
        return False

    @classmethod
    def is_allowed_refsname_pattern(self, name):
        if name is None or name == '' or len(name) > 1024:
            return False
        if re.match('^[a-zA-Z0-9_\-\.]+$', name) and not name.startswith('-'):
            return True
        return False

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
        for repo in repos:
            repo_vo = {}
            repo_vo['id'] = repo.id
            repo_vo['username'] = repo.username
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
    MERGED_FAILED = 1
    MERGED = 2
    REJECTED = 3
    CLOSE = 4

    VIEW_MAP = {
        0 : '未合并',
        1 : '合并失败',
        2 : '合并',
        3 : '拒绝',
        4 : '关闭',
    }

    LABEL_MAP = {
        0 : 'label-info',
        1 : 'label-warning',
        2 : 'label-success',
        3 : 'label-important',
        4 : 'label-inverse',
    }


