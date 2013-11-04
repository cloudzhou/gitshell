# -*- coding: utf-8 -*-
import os, re, pipes, sys, traceback, codecs, signal
import time, json, hashlib, shutil
from django.core.cache import cache
from subprocess import check_output, Popen, PIPE
from chardet.universaldetector import UniversalDetector
from gitshell.objectscache.models import CacheKey
from gitshell.gsuser.models import GsuserManager
from gitshell.repo.models import RepoManager
from gitshell.viewtools.views import json_httpResponse
from gitshell.settings import PULLREQUEST_REPO_PATH, logger
"""
git ls-tree `cat .git/refs/heads/master` -- githooks/
git log -1 --pretty='%ct %s' -- githooks/
git show HEAD:README.md
git diff 2497dbb67cb29c0448a3c658ed50255cb4de6419 a2f5ec702e58eb5053fc199c590eac29a2627ad7 --
path: . means is root of the repo path
"""
BINARY_FILE_TYPE = set(['doc', 'docx', 'msg', 'odt', 'pages', 'rtf', 'wpd', 'wps', 'azw', 'dat', 'efx', 'epub', 'gbr', 'ged', 'ibooks', 'key', 'keychain', 'pps', 'ppt', 'pptx', 'sdf', 'tar', 'vcf', 'aif', 'iff', 'm3u', 'm4a', 'mid', 'mp3', 'mpa', 'ra', 'wav', 'wma', '3g2', '3gp', 'asf', 'asx', 'avi', 'flv', 'mov', 'mp4', 'mpg', 'rm', 'srt', 'swf', 'vob', 'wmv', '3dm', '3ds', 'max', 'obj', 'bmp', 'dds', 'dng', 'gif', 'jpeg', 'jpg', 'png', 'webp', 'tiff', 'psd', 'pspimage', 'tga', 'thm', 'tif', 'yuv', 'ai', 'eps', 'ps', 'indd', 'pct', 'pdf', 'xlr', 'xls', 'xlsx', 'accdb', 'db', 'dbf', 'mdb', 'pdb', 'apk', 'app', 'com', 'exe', 'gadget', 'jar', 'pif', 'wsf', 'dem', 'gam', 'nes', 'rom', 'sav', 'dwg', 'dxf', 'gpx', 'cfm', 'crx', 'plugin', 'fnt', 'fon', 'otf', 'ttf', 'cab', 'cpl', 'cur', 'dll', 'dmp', 'drv', 'icns', 'ico', 'lnk', 'sys', 'prf', 'hqx', 'mim', 'uue', '7z', 'cbr', 'deb', 'gz', 'pkg', 'rar', 'rpm', 'sit', 'sitx', 'tar.gz', 'zip', 'zipx', 'bin', 'cue', 'dmg', 'iso', 'mdf', 'toast', 'vcd', 'class', 'fla', 'tmp', 'crdownload', 'ics', 'msi', 'part', 'torrent'])
class GitHandler():

    def __init__(self):
        self.empty_commit_hash = '0000000000000000000000000000000000000000'
        self.stage_path = '/opt/repo/stage'
        self.blank_p = re.compile(r'\s+')

    def repo_ls_tree(self, repo_path, commit_hash, path):
        (commit_hash, path) = self._all_to_utf8(commit_hash, path)
        if not self._path_check_chdir(repo_path, commit_hash, path):
            return {}
        origin_path = path
        path = self._get_quote_path(path)
        stage_file = self._get_stage_file(repo_path, commit_hash, path)
        result = self._read_load_stage_file(stage_file)
        if result is not None:
            return result
        result = self._ls_tree_check_output(commit_hash, path, origin_path)
        self._dumps_write_stage_file(result, stage_file)
        return result
    
    def repo_cat_file(self, repo_path, commit_hash, path):
        (commit_hash, path) = self._all_to_utf8(commit_hash, path)
        if not self._path_check_chdir(repo_path, commit_hash, path):
            return ''
        path = self._get_quote_path(path)
        if path.startswith('./'):
            path = path[2:]
        file_type = path.split('.')[-1]
        if file_type in BINARY_FILE_TYPE:
            return u'二进制文件'
        stage_file = self._get_stage_file(repo_path, commit_hash, path)
        result = self._read_load_stage_file(stage_file)
        if result is not None:
            return result['blob']
        command = '/usr/bin/git show %s:%s | /usr/bin/head -c 524288' % (commit_hash, path)
        try:
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
            result = check_output(command, shell=True)
            ud = UniversalDetector()
            ud.feed(result)
            ud.close()
            if ud.result['encoding']:
                encoding = ud.result['encoding']
                if encoding != 'utf-8' or encoding != 'utf8':
                    result = result.decode(encoding).encode('utf-8')
            self._dumps_write_stage_file({'blob': result}, stage_file)
            return result
        except Exception, e:
            logger.exception(e)
        finally: 
            signal.signal(signal.SIGPIPE, signal.SIG_IGN)
        return ''
    
    def repo_log_file(self, repo_path, from_commit_hash, commit_hash, log_size, path):
        (from_commit_hash, commit_hash, path) = self._all_to_utf8(from_commit_hash, commit_hash, path)
        if not self._path_check_chdir(repo_path, commit_hash, path) or not re.match('^\w+$', from_commit_hash):
            return {}
        path = self._get_quote_path(path)
        between_commit_hash = from_commit_hash + '...' + commit_hash
        stage_file = self._get_stage_file(repo_path, between_commit_hash, str(log_size) + '|' + path)
        stage_file = stage_file + '.log'
        result = self._read_load_stage_file(stage_file)
        if result is not None:
            return result
        result = self._repo_load_log_file(from_commit_hash, commit_hash, log_size, path)
        self._dumps_write_stage_file(result, stage_file)
        return result

    def repo_diff(self, repo_path, pre_commit_hash, commit_hash, context, path):
        if not context:
            context = 3
        (pre_commit_hash, commit_hash, path) = self._all_to_utf8(pre_commit_hash, commit_hash, path)
        if not self._path_check_chdir(repo_path, commit_hash, path) or not re.match('^\w+$', pre_commit_hash):
            return {}
        path = self._get_quote_path(path)
        stage_file = self._get_diff_stage_file(repo_path, pre_commit_hash, commit_hash, context, path)
        stage_file = stage_file + '.diff'
        result = self._read_load_stage_file(stage_file)
        if result is not None:
            return result['diff']
        command = '/usr/bin/git diff --numstat  %s..%s -- %s | /usr/bin/head -c 524288 ; /usr/bin/git diff -U%s %s..%s -- %s | /usr/bin/head -c 524288' % (pre_commit_hash, commit_hash, path, context, pre_commit_hash, commit_hash, path)
        try:
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
            result = check_output(command, shell=True)
            diff = self._parse_diff_file_as_json(result)
            self._dumps_write_stage_file({'diff': diff}, stage_file)
            return diff
        except Exception, e:
            logger.exception(e)
        finally: 
            signal.signal(signal.SIGPIPE, signal.SIG_IGN)
        return {}

    def repo_log_graph(self, repo, repo_path, commit_hash):
        if not self._path_check_chdir(repo_path, commit_hash, '.') or not re.match('^\w+$', commit_hash):
            return {}
        stage_file = self._get_stage_file(repo_path, commit_hash, repo.last_push_time)
        stage_file = stage_file + '.lg'
        log_graph = self._read_load_stage_file(stage_file)
        if log_graph is not None:
            return log_graph
        command = '/usr/bin/git log -100 --graph --abbrev-commit --date=relative --format=format:"%%h - (%%ar) %%s - %%an%%d" %s | /usr/bin/head -c 524288' % (commit_hash)
        try:
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
            log_graph = check_output(command, shell=True)
            log_graph_json = {'log_graph': log_graph}
            self._dumps_write_stage_file(log_graph_json, stage_file)
            return log_graph_json
        except Exception, e:
            logger.exception(e)
        finally: 
            signal.signal(signal.SIGPIPE, signal.SIG_IGN)
        return {'log_graph': ''}
        
    def repo_ls_refs(self, repo, repo_path):
        if repo.status != 0 or not os.path.exists(repo_path):
            return  {'branches': [], 'tags': [], 'commit_hash': {}}
        meta = self._get_repo_meta(repo)
        return meta

    """ refs: branch, tag """
    def get_commit_hash(self, repo, repo_path, refs):
        if repo.status != 0 or not os.path.exists(repo_path):
            return self.empty_commit_hash
        meta = self._get_repo_meta(repo)
        if refs in meta['commit_hash']:
            return meta['commit_hash'][refs]
        if re.match('^\w+$', refs):
            return refs
        return self.empty_commit_hash

    def prepare_pull_request(self, source_repo, desc_repo):
        pullrequest_repo_path = '%s/%s/%s' % (PULLREQUEST_REPO_PATH, desc_repo.username, desc_repo.name)
        source_abs_repopath = source_repo.get_abs_repopath()
        source_remote_name = '%s-%s' % (source_repo.username, source_repo.name)
        dest_abs_repopath = desc_repo.get_abs_repopath()
        desc_remote_name = '%s-%s' % (desc_repo.username, desc_repo.name)
        action = 'prepare'
        args = [pullrequest_repo_path, source_abs_repopath, source_remote_name, dest_abs_repopath, desc_remote_name, action]
        if not self._is_allowed_paths(args):
            return False
        args = ['/bin/bash', '/opt/bin/git-pullrequest.sh'] + args
        try:
            popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
            output = popen.communicate()[0].strip()
            return popen.returncode == 0
        except Exception, e:
            logger.exception(e)
        return False

    def merge_pull_request(self, source_repo, desc_repo, source_refs, desc_refs, merge_commit_message):
        pullrequest_repo_path = '%s/%s/%s' % (PULLREQUEST_REPO_PATH, desc_repo.username, desc_repo.name)
        source_abs_repopath = source_repo.get_abs_repopath()
        source_remote_name = '%s-%s' % (source_repo.username, source_repo.name)
        dest_abs_repopath = desc_repo.get_abs_repopath()
        desc_remote_name = '%s-%s' % (desc_repo.username, desc_repo.name)
        action = 'merge'
        args = [pullrequest_repo_path, source_abs_repopath, source_remote_name, dest_abs_repopath, desc_remote_name, action, source_refs, desc_refs]
        if not self._is_allowed_paths(args):
            return (128, '合并失败，请检查是否存在冲突 或者 non-fast-forward')
        args = ['/bin/bash', '/opt/bin/git-pullrequest.sh'] + args + [merge_commit_message]
        try:
            popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
            output = popen.communicate()[0].strip()
            return (popen.returncode, output)
        except Exception, e:
            logger.exception(e)
        return (128, '合并失败，请检查是否存在冲突 或者 non-fast-forward')

    def create_branch(self, repo, branch, base_branch):
        if not self._is_allowed_path(branch) or not self._is_allowed_path(base_branch):
            return False
        refs_meta = self.repo_ls_refs(repo, repo.get_abs_repopath())
        if branch in refs_meta['branches'] or base_branch not in refs_meta['branches']:
            return False
        args = ['/usr/bin/git', 'branch', branch, base_branch]
        return self._run_command_on_repo_and_flush(repo, args)

    def create_tag(self, repo, tag, base_branch):
        if not self._is_allowed_path(tag) or not self._is_allowed_path(base_branch):
            return False
        refs_meta = self.repo_ls_refs(repo, repo.get_abs_repopath())
        if tag in refs_meta['tags'] or base_branch not in refs_meta['branches']:
            return False
        args = ['/usr/bin/git', 'tag', tag, base_branch]
        return self._run_command_on_repo_and_flush(repo, args)

    def delete_branch(self, repo, branch):
        if not self._is_allowed_path(branch):
            return False
        refs_meta = self.repo_ls_refs(repo, repo.get_abs_repopath())
        if branch not in refs_meta['branches']:
            return False
        args = ['/usr/bin/git', 'branch', '-D', branch]
        return self._run_command_on_repo_and_flush(repo, args)

    def delete_tag(self, repo, tag):
        if not self._is_allowed_path(tag):
            return False
        refs_meta = self.repo_ls_refs(repo, repo.get_abs_repopath())
        if tag not in refs_meta['tags']:
            return False
        args = ['/usr/bin/git', 'tag', '-d', tag]
        return self._run_command_on_repo_and_flush(repo, args)

    def update_server_info(self, repo):
        args = ['/usr/bin/git', 'update-server-info']
        return self._run_command_on_repo(repo, args)

    def _run_command_on_repo_and_flush(self, repo, args):
        if self._run_command_on_repo(repo, args):
            self.update_server_info(repo)
            cache.delete(CacheKey.REPO_COMMIT_VERSION % repo.id)
            return True
        return False

    def _run_command_on_repo(self, repo, args):
        abs_repopath = repo.get_abs_repopath()
        if os.path.exists(abs_repopath):
            self._chdir(abs_repopath)
            try:
                popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
                output = popen.communicate()[0].strip()
                return popen.returncode == 0
            except Exception, e:
                logger.exception(e)
        return False

    def _repo_load_log_file(self, from_commit_hash, commit_hash, log_size, path):
        commits = []
        between_commit_hash = commit_hash
        
        path_in_git = ''
        if path != '' and path != '.':
            path_in_git = '-- ' + path
        if from_commit_hash is not None and not from_commit_hash.startswith('0000000'):
            between_commit_hash = from_commit_hash + '...' + commit_hash
        command = '/usr/bin/git log -%s --pretty="%%h|%%p|%%t|%%an|%%ae|%%at|%%cn|%%ce|%%ct|%%s" %s %s | /usr/bin/head -c 524288' % (log_size, between_commit_hash, path_in_git)
        try:
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
            raw_result = check_output(command, shell=True)
            for line in raw_result.split('\n'):
                ars = line.split('|', 9)
                if len(ars) != 10:
                    continue
                (commit_hash, parent_commit_hash, tree_hash, author_name, author_email, author_date, committer_name, committer_email, committer_date, commit_message) = (ars)
                commit = {
                    'commit_hash': commit_hash,
                    'parent_commit_hash': parent_commit_hash,
                    'tree_hash': tree_hash,
                    'author_name': author_name,
                    'author_email': author_email,
                    'author_date': author_date,
                    'committer_name': committer_name,
                    'committer_email': committer_email,
                    'committer_date': committer_date,
                    'commit_message': commit_message,
                }
                commit['parent_commit_hash'] = parent_commit_hash.split(' ')
                self._set_real_author_committer_name(commit)
                commits.append(commit)
            return commits
        except Exception, e:
            logger.exception(e)
        finally: 
            signal.signal(signal.SIGPIPE, signal.SIG_IGN)
        return []
    
    def _ls_tree_check_output(self, commit_hash, path, origin_path):
        command = 'git config --global core.quotepath false; /usr/bin/git ls-tree %s -- %s | /usr/bin/head -c 524288' % (commit_hash, path)
        tree = {}; dirs = []; files = []; has_readme = False; readme_file = '';
        try:
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
            raw_output = check_output(command, shell=True)
            max = 500
            for line in raw_output.split("\n"):
                array = self.blank_p.split(line, 3) 
                if len(array) >= 4:
                    abs_path = array[3]; relative_path = abs_path
                    if path != '.':
                        relative_path = abs_path[len(origin_path):]
                    if array[1] == 'tree':
                        relative_path = relative_path + '/'
                    relative_path = self._oct_utf8_decode(relative_path)
                    if self._repo_file_path_check(relative_path):
                        tree[relative_path] = {}
                        tree[relative_path]['relative_path'] = relative_path
                        tree[relative_path]['type'] = array[1]
                        tree[relative_path]['commit_hash'] = array[2]
                        tree[relative_path]['abs_path'] = abs_path
                        filename_lower = relative_path.lower()
                        if filename_lower == 'readme.md' or filename_lower == 'readme.mkd':
                            has_readme = True
                            readme_file = abs_path
                        if array[1] == 'tree':
                            dirs.append(relative_path)
                        else:
                            files.append(relative_path)
                if(max <= 0):
                    break
                max = max - 1
            quote_relative_paths = []
            for relative_path in tree.keys():
                quote_relative_paths.append(pipes.quote(relative_path))
            if len(path.split('/')) < 50 and '"' not in origin_path:
                pre_path = origin_path
                if path == '.':
                    pre_path = ''
                last_commit_command = 'for i in %s; do echo -n "$i|"; git log %s -1 --pretty="%%at|%%an|%%ae|%%s" -- "%s$i" | /usr/bin/head -c 524288; done' % (' '.join(quote_relative_paths), commit_hash, pre_path)
                last_commit_output = check_output(last_commit_command, shell=True)
                for last_commit in last_commit_output.split('\n'):
                    splits = last_commit.split('|', 4)
                    if len(splits) < 5:
                        continue
                    relative_path = splits[0]
                    tree[relative_path]['author_time'] = splits[1]
                    tree[relative_path]['author_name'] = splits[2]
                    tree[relative_path]['author_email'] = splits[3]
                    tree[relative_path]['last_commit_message'] = splits[4]
            dirs.sort()
            files.sort()
            ordered_tree = []
            for file_path in dirs + files:
                tree_item = tree[file_path]
                self._set_real_author_name(tree_item)
                ordered_tree.append(tree_item)
            return {'tree': ordered_tree, 'has_readme': has_readme, 'readme_file': readme_file}
        except Exception, e:
            logger.exception(e)
        finally: 
            signal.signal(signal.SIGPIPE, signal.SIG_IGN)
        return {}

    def _set_real_author_name(self, item):
        if 'author_name' not in item or 'author_email' not in item:
            return
        author_name = item['author_name']
        author_email = item['author_email']
        item['real_author_name'] = ''
        user = GsuserManager.get_user_by_email(author_email)
        if user:
            item['real_author_name'] = user.username
            return
        user = GsuserManager.get_user_by_name(author_name)
        if user:
            item['real_author_name'] = user.username

    def _set_real_committer_name(self, item):
        if 'committer_name' not in item or 'committer_email' not in item:
            return
        committer_name = item['committer_name']
        committer_email = item['committer_email']
        item['real_committer_name'] = ''
        user = GsuserManager.get_user_by_email(committer_email)
        if user:
            item['real_committer_name'] = user.username
            return
        user = GsuserManager.get_user_by_name(committer_name)
        if user:
            item['real_committer_name'] = user.username

    def _set_real_author_committer_name(self, commit):
        self._set_real_author_name(commit)
        self._set_real_committer_name(commit)

    def _get_diff_stage_file(self, repo_path, pre_commit_hash, commit_hash, context, path):
        (username, reponame) = repo_path.split('/')[-2:]
        identity = '%s|%s|%s|%s' % (pre_commit_hash, commit_hash, context, path)
        stage_file = '%s/%s/%s/%s' % (self.stage_path, username, reponame, hashlib.md5(identity).hexdigest())
        return stage_file

    def _get_stage_file(self, repo_path, commit_hash, uniq_str):
        (username, reponame) = repo_path.split('/')[-2:]
        identity = '%s|%s' % (commit_hash, uniq_str)
        stage_file = '%s/%s/%s/%s' % (self.stage_path, username, reponame, hashlib.md5(identity).hexdigest())
        return stage_file
        
    def _read_load_stage_file(self, stage_file):
        if not os.path.exists(stage_file):
            return None
        try:
            with codecs.open(stage_file, encoding='utf-8', mode='r') as json_data:
                result = json.load(json_data)
                return result
        except Exception, e:
            logger.exception(e)
        return None

    def _dumps_write_stage_file(self, result, stage_file):
        if result is None:
            return
        timenow = int(time.time()) 
        stage_file_tmp = '%s.%s' % (stage_file, timenow)
        stage_file_tmp_path = os.path.dirname(stage_file_tmp)
        if not os.path.exists(stage_file_tmp_path):
            os.makedirs(stage_file_tmp_path)
        try:
            with codecs.open(stage_file_tmp, encoding='utf-8', mode='w') as stage_file_w:
                stage_file_w.write(json.dumps(result))
                stage_file_w.flush()
                shutil.move(stage_file_tmp, stage_file)
        except Exception, e:
            logger.exception(e)
        finally:
            if os.path.exists(stage_file_tmp):
                os.remove(stage_file_tmp)

    def _get_quote_path(self, path):
        path = ''.join(c for c in path if ord(c) >= 32 and ord(c) != 127)
        path = pipes.quote(path)
        if isinstance(path, unicode):
            path = path.encode('utf8')
        return path
        
    def _repo_file_path_check(self, path):
        if re.match('.*[\@\#\$\&\\\*\"\'\<\>\|\;].*', path) or path.startswith('-') or len(path) > 512 or len(path.split('/')) > 100:
            return False
        return True

    def _path_check_chdir(self, repo_path, commit_hash, path):
        if repo_path is None or commit_hash is None or path is None:
            return False
        if not os.path.exists(repo_path) or not self._is_allowed_path(repo_path) or not re.match('^\w+$', commit_hash):
            return False
        if not self._repo_file_path_check(path):
            return False
        if len(repo_path) > 512 or self._chdir(repo_path) is False or len(commit_hash) > 512:
            return False
        return True
    
    def _get_repo_meta(self, repo):
        meta = self._get_repo_meta_by_cache(repo)
        if meta is not None:
            return meta
        branches = []
        tags = []
        commit_hash_dict = {}
        meta = {'branches': branches, 'tags': tags, 'commit_hash': commit_hash_dict}

        repo_path = repo.get_abs_repopath();
        heads_path = '%s/refs/heads' % (repo_path)
        tags_path = '%s/refs/tags' % (repo_path)
        self._append_refs_and_put_dict(heads_path, branches, commit_hash_dict)
        self._append_refs_and_put_dict(tags_path, tags, commit_hash_dict)

        blank_p = re.compile(r'\s+')
        refs_heads = 'refs/heads/'
        refs_tags = 'refs/tags/'
        refs_path = '%s/packed-refs' % repo_path
        info_refs_path = '%s/info/refs' % repo_path
        if os.path.exists(info_refs_path):
            refs_path = info_refs_path
        if os.path.exists(refs_path):
            refs_f = None
            try:
                refs_f = open(refs_path, 'r')
                for line in refs_f:
                    if line.startswith('#'):
                        continue
                    if len(branches) >= 100 or len(tags) >= 100:
                        break
                    array = blank_p.split(line)
                    if len(array) < 2:
                        continue
                    commit_hash = array[0].strip()
                    refs_from_f = array[1].strip()
                    if not re.match('^\w+$', commit_hash) or not self._is_allowed_path(refs_from_f):
                        continue
                    if refs_from_f.startswith(refs_heads):
                        refs = refs_from_f[len(refs_heads):]
                        if refs not in branches:
                            branches.append(refs)
                        commit_hash_dict[refs] = commit_hash
                    elif refs_from_f.startswith(refs_tags):
                        refs = refs_from_f[len(refs_tags):]
                        if refs not in tags:
                            tags.append(refs)
                        commit_hash_dict[refs] = commit_hash
            finally:
                if refs_f != None:
                    refs_f.close()
        meta['branch_count'] = len(branches)
        meta['tag_count'] = len(tags)
        self._repo_meta_sort_refs(branches, tags)
        self._repo_meta_refs_detail_commit(repo, meta, commit_hash_dict)
        self._cache_repo_meta(repo, meta)
        return meta

    def _repo_meta_sort_refs(self, branches, tags):
        branches.sort()
        if 'master' in branches:
            branches.remove('master')
            branches.insert(0, 'master')
        tags.sort()
        tags.reverse()

    def _repo_meta_refs_detail_commit(self, repo, meta, commit_hash_dict):
        if not self._chdir(repo.get_abs_repopath()):
            return
        refs_detail_commit = {}
        refses = commit_hash_dict.keys()
        try:
            last_commit_command = '/bin/bash -c \'for i in %s; do echo -n "$i|"; git log "$i" -1 --pretty="%%h|%%p|%%t|%%an|%%ae|%%at|%%cn|%%ce|%%ct|%%s" | /usr/bin/head -c 524288; done\'' % (' '.join(refses))
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
            last_commit_output = check_output(last_commit_command, shell=True)
            for line in last_commit_output.split('\n'):
                ars = line.split('|', 10)
                if len(ars) != 11:
                    continue
                (refs, commit_hash, parent_commit_hash, tree_hash, author_name, author_email, author_date, committer_name, committer_email, committer_date, commit_message) = (ars)
                refs_commit = {
                    'commit_hash': commit_hash,
                    'parent_commit_hash': parent_commit_hash,
                    'tree_hash': tree_hash,
                    'author_name': author_name,
                    'author_email': author_email,
                    'author_date': author_date,
                    'committer_name': committer_name,
                    'committer_email': committer_email,
                    'committer_date': committer_date,
                    'commit_message': commit_message,
                }
                refs_commit['parent_commit_hash'] = parent_commit_hash.split(' ')
                self._set_real_author_committer_name(refs_commit)
                refs_detail_commit[refs] = refs_commit
        except Exception, e:
            logger.exception(e)
        finally: 
            signal.signal(signal.SIGPIPE, signal.SIG_IGN)
        meta['detail_commit'] = refs_detail_commit

    def _get_repo_meta_by_cache(self, repo):
        cacheKey = CacheKey.REPO_COMMIT_VERSION % repo.id
        version = cache.get(cacheKey)
        if version is not None:
            cacheKey = CacheKey.REPO_META % (repo.id, version)
            repo_meta = cache.get(cacheKey)
            if repo_meta is not None:
                return repo_meta
        return None

    def _cache_repo_meta(self, repo, meta):
        cacheKey = CacheKey.REPO_COMMIT_VERSION % repo.id
        version = cache.get(cacheKey)
        if version is None:
            version = time.time()
            cache.add(cacheKey, version, 3600)
        cacheKey = CacheKey.REPO_META % (repo.id, version)
        cache.add(cacheKey, meta, 3600)

    def _append_refs_and_put_dict(self, dirpath, refs_array, commit_hash_dict):
        for refs in os.listdir(dirpath):
            if not self._is_allowed_path(refs):
                continue
            if len(refs_array) >= 100:
                return
            if refs in refs_array:
                continue
            refs_array.append(refs)
            refs_path = '%s/%s' % (dirpath, refs)
            f = None
            try:
                f = open(refs_path, 'r')
                commit_hash = f.read(40)
                if re.match('^\w+$', commit_hash):
                    commit_hash_dict[refs] = commit_hash
            finally:
                if f != None:
                    f.close()
    
    def _is_allowed_paths(self, paths):
        for path in paths:
            if not self._is_allowed_path(path):
                return False
        return True

    def _is_allowed_path(self, path):
        if '..' in path or path.startswith('-'):
            return False
        if re.match('^[a-zA-Z0-9_\.\-/]+$', path):
            return True
        return False

    def _chdir(self, path):
        try:
            os.chdir(path)
            return True
        except Exception, e:
            logger.exception(e)
        return False

    def _all_to_utf8(self, *args):
        return tuple([x.encode('utf8') if x is not None and isinstance(x, unicode) else x for x in args])

    def _oct_utf8_decode(self, oct_utf8_encode):
        if not oct_utf8_encode.startswith('\"') or not oct_utf8_encode.endswith('\"'):
            return oct_utf8_encode
        oct_utf8_encode = oct_utf8_encode[1:len(oct_utf8_encode)-1]
        oct_utf8_encode_len = len(oct_utf8_encode)
        raw_chars = []
        i = 0
        while i < oct_utf8_encode_len:
            if oct_utf8_encode[i] == '\\' and i < oct_utf8_encode_len - 3 and oct_utf8_encode[i+1].isdigit() and oct_utf8_encode[i+2].isdigit() and oct_utf8_encode[i+3].isdigit():
                raw_chars.append(chr(int(oct_utf8_encode[i+1:i+4], 8)))
                i = i + 4
                continue
            if oct_utf8_encode[i] == '\\' and i < oct_utf8_encode_len - 1:
                raw_chars.append(oct_utf8_encode[i+1])
                i = i + 2
                continue
            raw_chars.append(oct_utf8_encode[i])
            i = i + 1
        return ''.join(raw_chars)

    def _parse_diff_file_as_json(self, raw_diff):
        diff = {}
        lines = raw_diff.split('\n')
        blank_p = re.compile(r'\s+')
        lines_len = len(lines)
        numstat = []
        i = 0
        while i < lines_len:
            line = lines[i]
            if not re.match('\d+\s+\d+\s+\S', line):
                break
            numstat.append(blank_p.split(line, 2))
            i = i + 1
        detail = []
        diff['numstat'] = numstat; diff['detail'] = detail
        
        filea = '--- '; fileb = '+++ '
        filea_len = len(filea); fileb_len = len(fileb)
        dev_null = '/dev/null'
        
        filediff = {}; filename = ''; linediff = []; part_of_linediff = []
        starta = 0; startb = 0; start_line_stat = False
        
        while i < lines_len:
            line = lines[i]
            if start_line_stat:
                if line.startswith(' '):
                    part_of_linediff.append([starta, startb, line[1:]])
                    starta = starta + 1; startb = startb + 1
                    i = i + 1
                    continue
                if line.startswith('+'):
                    part_of_linediff.append([0, startb, line[1:]])
                    startb = startb + 1
                    i = i + 1
                    continue
                if line.startswith('-'):
                    part_of_linediff.append([starta, 0, line[1:]])
                    starta = starta + 1
                    i = i + 1
                    continue
            start_line_stat = False
            if line.startswith('diff --git'):
                if filename != '' and filediff and 'mode' in filediff:
                    if len(part_of_linediff) > 0:
                        linediff.append(part_of_linediff)
                    filediff['linediff'] = linediff
                    filediff['filename'] = filename
                    detail.append(filediff)
                filediff = {}
                filename = ''
                linediff = []
                part_of_linediff = []
            if line.startswith(filea):
                filediff['from'] = line[filea_len:]
            if line.startswith(fileb):
                filediff['to'] = line[fileb_len:]
            if 'mode' not in filediff and 'from' in filediff and 'to' in filediff:
                mode = 'edit'
                filename = filediff['to'][2:]
                if filediff['from'] == dev_null and filediff['to'] != dev_null:
                    mode = 'create'
                if filediff['from'] != dev_null and filediff['to'] == dev_null:
                    mode = 'delete'
                    filename = filediff['from'][2:]
                filediff['mode'] = mode
            m = re.match('^@@ \-(\d+),\d+ \+(\d+)', line)
            if m:
                if len(part_of_linediff) > 0:
                    linediff.append(part_of_linediff)
                part_of_linediff = []
                starta = int(m.group(1))
                startb = int(m.group(2))
                start_line_stat = True
            i = i + 1
        
        if filename != '' and filediff and 'mode' in filediff:
            if len(part_of_linediff) > 0:
                linediff.append(part_of_linediff)
            filediff['linediff'] = linediff
            filediff['filename'] = filename
            detail.append(filediff)
        diff['changedfiles_count'] = len(numstat)
        total_add_line = 0; total_delete_line = 0;
        for item in numstat:
            total_add_line = total_add_line + int(item[0])
            total_delete_line = total_delete_line + int(item[1])
        abs_change_line = total_add_line - total_delete_line
        diff['total_add_line'] = total_add_line
        diff['total_delete_line'] = total_delete_line
        diff['abs_change_line'] = abs_change_line
        return diff

if __name__ == '__main__':
    gitHandler = GitHandler()
    #print gitHandler.repo_ls_branches('/opt/8001/gitshell/.git')
    #print gitHandler.get_commit_hash('/opt/8001/gitshell/.git', 'refs/heads/master')
    print gitHandler._is_allowed_path('abc')
    print gitHandler._is_allowed_path('abc b')
    print gitHandler._is_allowed_path('abc-_/.b')
    print gitHandler.repo_ls_tree('/opt/8001/gitshell/.git', '16d71ee5f6131254c7865951bf277ffe4bde1cf9', 'githooks/')
    print gitHandler.repo_ls_tree('/opt/8001/gitshell/.git', '16d71ee5f6131254c7865951bf277ffe4bde1cf9', '.')
    print gitHandler.repo_cat_file('/opt/8001/gitshell/.git', '16d71ee5f6131254c7865951bf277ffe4bde1cf9', 'README.md')
    print gitHandler.repo_log_file('/opt/8001/gitshell/.git', '16d71ee5f6131254c7865951bf277ffe4bde1cf9', '0000000', 50, 'README.md')
    print gitHandler.repo_diff('/opt/8001/gitshell/.git', '7daf915', '1e25868', 3, 'README.md')
