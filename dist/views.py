# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.cache import cache
import re

def repos(request, username, projectname):
    global project_partition_array
    if len(project_partition_array) == 0:
        refresh(request)
    hashcode = abs(hash(username) % 1024)
    for project_partition in project_partition_array:
        if hashcode >= project_partition.from_index and hashcode <= project_partition.to_index:
            return HttpResponse(project_partition.host + ' ' + repos_root, content_type="text/plain")
    return HttpResponse("auth and distributed", content_type="text/plain")

def refresh(request):
    global project_partition_array
    new_repos_partition_array = []
    file = open(project_partition_conf_file, 'r')
    try:
        for line in file:
            array = re.sub("\s+", " ", line.strip()).split(" ")
            if len(array) != 3 or not re.match("\d+", array[0]) or not re.match("\d+", array[1]):
                continue
            project_partition  = ProjectPartition(int(array[0]), int(array[1]), array[2])
            new_repos_partition_array.append(project_partition)
    finally:
        file.close()
    if len(new_repos_partition_array) > 0:
        project_partition_array = new_repos_partition_array
    
    return echo(request)

def echo(request):
    global project_partition_array
    if len(project_partition_array) == 0:
        refresh(request)
    str_list = []
    for project_partition in project_partition_array:
        str_list.append(str(project_partition))
    return HttpResponse('\n'.join(str_list), content_type="text/plain")

# static field and class
repos_root = '/opt/repos'
project_partition_array = []
project_partition_conf_file = "/opt/run/var/project_partition.conf"

class ProjectPartition:
    def __init__(self, from_index, to_index, host):
        self.from_index = from_index
        self.to_index = to_index
        self.host = host
    def __str__(self):
        return ' '.join([str(self.from_index), str(self.to_index), self.host])
