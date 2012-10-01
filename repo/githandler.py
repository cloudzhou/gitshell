#!/python
# -*- coding: utf-8 -*-
import os, re
import time
import json
import hashlib
import shutil
from subprocess import check_output
from gitshell.viewtools.views import json_httpResponse
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
        if not self.path_check_chdir(repo_path, commit_hash, path):
            return None
        stage_file = self.get_stage_file(repo_path, commit_hash, path)
        result = self.read_load_stage_file(stage_file)
#        result = None
        if result is not None:
            return result
        result = self.ls_tree_check_output(commit_hash, path)
        self.dumps_write_stage_file(result, stage_file)
        return result
    
    def repo_cat_file(self, repo_path, commit_hash, path):
        if not self.path_check_chdir(repo_path, commit_hash, path):
            return None
        file_type = path.split('.')[-1]
        if file_type in BINARY_FILE_TYPE:
            return "二进制文件"
        stage_file = self.get_stage_file(repo_path, commit_hash, path)
        result = self.read_load_stage_file(stage_file)
        if result is not None:
            return result
        command = '/usr/bin/git show %s:%s | /usr/bin/head -c 524288' % (commit_hash, path)
        try:
            result = check_output(command, shell=True)
            self.dumps_write_stage_file(result, stage_file)
            return result
        except Exception, e:
            print e
            return None
    
    def repo_log_file(self, repo_path, commit_hash, path):
        if not self.path_check_chdir(repo_path, commit_hash, path):
            return None
        stage_file = self.get_stage_file(repo_path, commit_hash, path)
        stage_file = stage_file + '.log'
        result = self.read_load_stage_file(stage_file)
        if result is not None:
            return result
        result = self.repo_load_log_file(commit_hash, path)
        self.dumps_write_stage_file(result, stage_file)
        return result

    def repo_load_log_file(self, commit_hash, path):
        commits = []
        command = '/usr/bin/git log -10 --pretty="%%h______%%t______%%an______%%cn______%%ct|%%s" %s -- %s | /usr/bin/head -c 524288' % (commit_hash, path)
        try:
            raw_result = check_output(command, shell=True)
            for line in raw_result.split('\n'):
                ars = line.split('|', 1)
                if len(ars) != 2:
                    continue
                attr, commit_message = ars
                attrs = attr.split('______', 5)
                if len(attrs) != 5:
                    continue
                (commit_hash, tree_hash, author, committer, committer_date) = (attrs)
                commits.append({
                    'commit_hash': commit_hash,
                    'tree_hash': tree_hash,
                    'author': author,
                    'committer': committer,
                    'committer_date': committer_date,
                    'commit_message': commit_message,
                })
            return commits
        except Exception, e:
            print e
            return None
    
    def repo_diff(self, repo_path, pre_commit_hash, commit_hash, path):
        if not self.path_check_chdir(repo_path, commit_hash, path) or not re.match('^\w+$', pre_commit_hash):
            return None
        stage_file = self.get_diff_stage_file(repo_path, pre_commit_hash, commit_hash, path)
        stage_file = stage_file + '.diff'
        result = self.read_load_stage_file(stage_file)
        if result is not None:
            return result
        command = '/usr/bin/git diff %s..%s -- %s | /usr/bin/head -c 524288' % (pre_commit_hash, commit_hash, path)
        try:
            result = check_output(command, shell=True)
            self.dumps_write_stage_file(result, stage_file)
            return result
        except Exception, e:
            print e
            return None

    def get_diff_stage_file(self, repo_path, pre_commit_hash, commit_hash, path):
        (username, reponame) = repo_path.split('/')[-2:]
        stage_file = '%s/%s/%s/%s' % (self.stage_path, username, reponame, hashlib.md5('%s|%s|%s' % (pre_commit_hash, commit_hash, path)).hexdigest())
        return stage_file

    def get_stage_file(self, repo_path, commit_hash, path):
        (username, reponame) = repo_path.split('/')[-2:]
        stage_file = '%s/%s/%s/%s' % (self.stage_path, username, reponame, hashlib.md5('%s|%s' % (commit_hash, path)).hexdigest())
        return stage_file
        
    # TODO load or not ?
    def read_load_stage_file(self, stage_file):
        if os.path.exists(stage_file):
            try:
                json_data = open(stage_file)
                result = json.load(json_data)
                return result
            except Exception, e:
                print e
                return None
            finally:
                json_data.close()

    def ls_tree_check_output(self, commit_hash, path):
        command = '/usr/bin/git ls-tree %s -- %s | /usr/bin/head -c 524288' % (commit_hash, path)
        result = {}
        try:
            raw_result = check_output(command, shell=True)
            max = 100
            for line in raw_result.split("\n"):
                array = self.blank_p.split(line) 
                if len(array) >= 4:
                    relative_path = array[3]
                    if path != '.':
                        relative_path = relative_path[len(path):]
                    if array[1] == 'tree':
                        relative_path = relative_path + '/'
                    if self.is_allowed_path(relative_path):
                        result[relative_path] = array[1:3]
                if(max <= 0):
                    break
                max = max - 1
            if len(path.split('/')) < 30:
                pre_path = path
                if path == '.':
                    pre_path = ''
                last_commit_command = 'for i in %s; do echo -n "$i "; git log -1 --pretty="%%ct %%an %%s" -- %s$i | /usr/bin/head -c 524288; done' % (' '.join(result.keys()), pre_path)
                last_commit_output = check_output(last_commit_command, shell=True)
                for last_commit in last_commit_output.split('\n'):
                    last_commit_array = last_commit.split(' ', 3)
                    if len(last_commit_array) > 3:
                        (relative_path, unixtime, author_name, last_commit_message) = last_commit_array
                        result[relative_path].append(unixtime)
                        result[relative_path].append(author_name)
                        result[relative_path].append(last_commit_message)
            return result
        except Exception, e:
            print e
            return None

    def dumps_write_stage_file(self, result, stage_file):
        if result is None:
            return
        timenow = int(time.time()) 
        stage_file_tmp = '%s.%s' % (stage_file, timenow)
        stage_file_tmp_path = os.path.dirname(stage_file_tmp)
        if not os.path.exists(stage_file_tmp_path):
            os.makedirs(stage_file_tmp_path)
        try:
            stage_file_w = open(stage_file_tmp, 'w')
            stage_file_w.write(json.dumps(result))
            stage_file_w.flush()
            shutil.move(stage_file_tmp, stage_file)
        except Exception, e:
            print e
        finally:
            if os.path.exists(stage_file_tmp):
                os.remove(stage_file_tmp)
            stage_file_w.close()

    def path_check_chdir(self, repo_path, commit_hash, path):
        if not self.is_allowed_path(repo_path) or not self.is_allowed_path(path) or not re.match('^\w+$', commit_hash) or not os.path.exists(repo_path):
            return False
        if len(path.split('/')) > 50 or self.chdir(repo_path) is False:
            return False
        if len(repo_path) > 256 or len(commit_hash) > 256 or len(path) > 256:
            return False
        return True
    
    def repo_ls_tags(self, repo_path):
        tags = []
        dirpath = '%s/refs/tags' % repo_path
        if not self.is_allowed_path(dirpath) or not os.path.exists(dirpath):
            return tags
        max = 20
        for tag in os.listdir(dirpath):
            if self.is_allowed_path(tag):
                tags.append(tag)
                max = max - 1
                if(max <= 0):
                    break
        tags.sort()
        tags.reverse()
        return tags
    
    def repo_ls_branches(self, repo_path):
        branches = []
        dirpath = '%s/refs/heads' % repo_path
        if not self.is_allowed_path(dirpath) or not os.path.exists(dirpath):
            return branches
        max = 20
        for branch in os.listdir(dirpath):
            if self.is_allowed_path(branch):
                if branch == 'master':
                    branches.insert(0, branch)
                else:
                    branches.append(branch)
                max = max - 1
                if(max <= 0):
                    break
        return branches
    
    """ refs: branch, tag """
    def get_commit_hash(self, repo_path, refs):
        refs_path = '%s/refs/heads/%s' % (repo_path, refs)
        if not os.path.exists(refs_path):
            refs_path = '%s/refs/tags/%s' % (repo_path, refs)
        if not self.is_allowed_path(refs_path) or not os.path.exists(refs_path):
            return self.empty_commit_hash
        f = None
        try:
            f = open(refs_path, 'r')
            commit_hash = f.read(40)
            if re.match('^\w+$', commit_hash):
                return commit_hash
        finally:
            if f != None:
                f.close()
        return self.empty_commit_hash
    
    def is_allowed_path(self, path):
        if '..' in path:
            return False
        if re.match('^[a-zA-Z0-9_\.\-/]+$', path):
            return True
        return False

    def chdir(self, path):
        try:
            os.chdir(path)
            return True
        except Exception, e:
            print e
            return False

if __name__ == '__main__':
    gitHandler = GitHandler()
    print gitHandler.repo_ls_branches('/opt/8001/gitshell/.git')
    print gitHandler.get_commit_hash('/opt/8001/gitshell/.git', 'refs/heads/master')
    print gitHandler.is_allowed_path('abc')
    print gitHandler.is_allowed_path('abc b')
    print gitHandler.is_allowed_path('abc-_/.b')
    print gitHandler.repo_ls_tree('/opt/8001/gitshell/.git', '16d71ee5f6131254c7865951bf277ffe4bde1cf9', 'githooks/')
    print gitHandler.repo_ls_tree('/opt/8001/gitshell/.git', '16d71ee5f6131254c7865951bf277ffe4bde1cf9', '.')
    print gitHandler.repo_cat_file('/opt/8001/gitshell/.git', '16d71ee5f6131254c7865951bf277ffe4bde1cf9', 'README.md')
    print gitHandler.repo_log_file('/opt/8001/gitshell/.git', '16d71ee5f6131254c7865951bf277ffe4bde1cf9', 'README.md')
    print gitHandler.repo_diff('/opt/8001/gitshell/.git', '7daf915', '1e25868', 'README.md')
