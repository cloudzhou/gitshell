import os, re
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.models import User
from gitshell.repo.models import RepoManager
from gitshell.gsuser.models import GsuserManager
from gitshell.keyauth.models import UserPubkey, KeyauthManager
from gitshell.settings import PRIVATE_REPO_PATH, PUBLIC_REPO_PATH
from gitshell.dist.views import repo as dist_repo

def pubkey(request, fingerprint):
    userPubkey = KeyauthManager.get_userpubkey_by_fingerprint(fingerprint)
    if userPubkey is not None:
        return HttpResponse(userPubkey.key, content_type="text/plain")
    return HttpResponse("", content_type="text/plain")

def keyauth(request, fingerprint, command):
    command = command.strip()
    last_blank_idx = command.rfind(' ')
    if last_blank_idx == -1:
        return not_git_command()
    pre_command = command[0 : last_blank_idx]
    short_repo_path = command[last_blank_idx+1 :]
    if pre_command == '' or '"' in pre_command or '\'' in pre_command or short_repo_path == '':
        return not_git_command()

    first_repo_char_idx = -1
    slash_idx = -1
    last_repo_char_idx = -1
    for i in range(0, len(short_repo_path)):
        schar = short_repo_path[i]
        if first_repo_char_idx == -1 and re.match('\w', schar):
            first_repo_char_idx = i
        if schar == '/':
            slash_idx = i
        if re.match('\w', schar):
            last_repo_char_idx = i
    if not (first_repo_char_idx > -1 and first_repo_char_idx < slash_idx and slash_idx < last_repo_char_idx):
        return not_git_command()

    username = short_repo_path[first_repo_char_idx : slash_idx] 
    reponame = short_repo_path[slash_idx+1 : last_repo_char_idx+1]
    if reponame.endswith('.git'):
        reponame = reponame[0 : len(reponame)-4]
    if not (re.match('^\w+$', username) and re.match('^\w+$', reponame)):
        return not_git_command()
    
    user = GsuserManager.get_user_by_name(username)
    if user is None:
        return not_git_command()
    userprofile = GsuserManager.get_userprofile_by_id(user.id)
    if userprofile is None:
        return not_git_command()
    if userprofile.used_quote > userprofile.quote:
        return not_git_command()
    repo = RepoManager.get_repo_by_userId_name(user.id, reponame)
    if repo is None:
        return not_git_command()

    quote = userprofile.quote
    # author of the repo
    userPubkey = KeyauthManager.get_userpubkey_by_userId_fingerprint(user.id, fingerprint)
    if userPubkey is not None:
        return response_full_git_command(quote, pre_command, user, repo)

    # member of the repo
    userpubkeys = KeyauthManager.list_userpubkey_by_fingerprint(fingerprint)
    for userpubkey in userpubkeys:
        repoMember = RepoManager.get_repo_member(repo.id, userpubkey.user_id)
        if repoMember is not None:
            return response_full_git_command(quote, pre_command, user, repo)
    return not_git_command()

blocks_quote = {67108864 : 327680}
kbytes_quote = {67108864 : 1048576}
def response_full_git_command(quote, pre_command, user, repo):
    blocks = 327680
    kbytes = 1048576
    if quote in blocks_quote:
        blocks = blocks_quote[quote]
        kbytes = kbytes_quote[quote]
    abs_repopath = repo.get_abs_repopath(user.username)
    if not os.path.exists(abs_repopath):
        return not_git_command()
    return HttpResponse("ulimit -f %s && ulimit -m %s && ulimit -v %s && /usr/bin/git-shell -c \"%s '%s'\"" % (blocks, kbytes, kbytes, pre_command, repo.get_abs_repopath(user.username)), content_type="text/plain")

def not_git_command():
    return HttpResponse("'git repoitory size limit exceeded or you have not rights or does not appear to be a git command'", content_type="text/plain")
    #return HttpResponse("/bin/echo \"fatal: git repoitory size limit exceeded or you have not rights or does not appear to be a git command\"", content_type="text/plain")

# echo -e "       _ _       _          _ _ \n      (_) |     | |        | | |\n  __ _ _| |_ ___| |__   ___| | |\n / _\` | | __/ __| '_ \ / _ \ | |\n| (_| | | |_\__ \ | | |  __/ | |\n \__, |_|\__|___/_| |_|\___|_|_|\n  __/ |                         \n |___/                          \nusage\n    help: get the help message\n    ls yourname: ls yournam's repo\n    mkdir yourname/reponame: create private repo for user yourname\n"

