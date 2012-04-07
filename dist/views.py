# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.cache import cache
import re

def repos(request, pproject):
    
    if len(project_partition_array) == 0:
        refresh(request)
    return HttpResponse("auth and distributed", content_type="text/plain")

def refresh(request):
    new_repos_partition_array = []
    file = open(project_partition_conf_file, 'r')
    try:
        for line in file:
            array = re.sub("\s+", " ", line.strip()).split(" ")
            if len(array) != 4 or not re.match("\d+", array[0]) or not re.match("\d+", array[1]) or not re.match("\d+", array[3]):
                continue
            project_partition  = ProjectPartition(int(array[0]), int(array[1]), array[2], int(array[3]))
            new_repos_partition_array.append(project_partition)
    finally:
        file.close()
    if len(new_repos_partition_array) > 0:
        project_partition_array = new_repos_partition_array
    
    return echo_repos_partition(request)

def echo_repos_partition(request):
    str_list = []
    for project_partition in project_partition_array:
        str_list.append(project_partition)

    return HttpResponse('\n'.join(str_list), content_type="text/plain")

# static field and class
project_partition_array = []
project_partition_conf_file = "/opt/run/var/project_partition.conf"

class ProjectPartition:
    def __init__(self, from_index, to_index, host, reposIndex):
        self.from_index = from_index
        self.to_index = to_index
        self.host = host
        self.reposIndex = reposIndex
    def __str__(self):
        return ' '.join([self.from_index, self.to_index, self.host, self.reposIndex])
