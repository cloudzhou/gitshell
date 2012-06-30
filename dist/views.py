from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.cache import cache
import re

def repo(request, username, reponame):
    repo_partition = get_repo_partition(username, reponame)
    if repo_partition is not None:
        return HttpResponse(repo_partition.host + ' ' + repo_root, content_type="text/plain")
    return HttpResponse("auth and distributed", content_type="text/plain")

def refresh(request):
    do_refresh()
    return echo(request)

def echo(request):
    global repo_partition_array
    str_list = []
    for repo_partition in repo_partition_array:
        str_list.append(str(repo_partition))
    return HttpResponse('\n'.join(str_list), content_type="text/plain")

def get_repo_partition(username, reponame):
    global repo_partition_array
    if len(repo_partition_array) == 1:
        return repo_partition_array[0]
    hashcode = abs(hash(username) % 1024)
    for repo_partition in repo_partition_array:
        if hashcode >= repo_partition.from_index and hashcode <= repo_partition.to_index:
            return repo_partition
    return None

def do_refresh():
    global repo_partition_array
    new_repo_partition_array = []
    file = open(repo_partition_conf_file, 'r')
    try:
        for line in file:
            array = re.sub("\s+", " ", line.strip()).split(" ")
            if len(array) != 3 or not re.match("\d+", array[0]) or not re.match("\d+", array[1]):
                continue
            repo_partition  = RepoPartition(int(array[0]), int(array[1]), array[2])
            new_repo_partition_array.append(repo_partition)
    finally:
        file.close()
    if len(new_repo_partition_array) > 0:
        repo_partition_array = new_repo_partition_array

# static field and class
repo_root = '/opt/repo/'
repo_partition_array = []
repo_partition_conf_file = "/opt/run/var/repo_partition.conf"

class RepoPartition:
    def __init__(self, from_index, to_index, host):
        self.from_index = from_index
        self.to_index = to_index
        self.host = host
    def __str__(self):
        return ' '.join([str(self.from_index), str(self.to_index), self.host])

do_refresh()
