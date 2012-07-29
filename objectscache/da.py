# -*- coding: utf-8 -*-  
from django.core.cache import cache
from django.db import connection, transaction
from gitshell.objectscache.models import Count
import time

rawsql = {
    # userpubkey #
    'userpubkey_l_userId':
        'select * from keyauth_userpubkey where visibly = 0 and user_id = %s limit 0, 10',
    'userpubkey_u_id':
        'update keyauth_userpubkey set visibly = 1 where visibly = 0 and user_id = %s and id = %s',
    'userpubkey_c_fingerprint':
        'select 0 as id, count(1) as count from keyauth_userpubkey where visibly = 0 and fingerprint = %s limit 0, 10',
    'userpubkey_s_fingerprint':
        'select * from keyauth_userpubkey where visibly = 0 and fingerprint = %s limit 0, 1',
    'userpubkey_s_userId_fingerprint':
        'select * from keyauth_userpubkey where visibly = 0 and user_id = %s and fingerprint = %s limit 0, 1',
    # user #
    'recommend_l_userId':
        'select * from gsuser_recommend where visibly = 0 and user_id = %s order by modify_time desc limit %s, %s',
    # repo #
    'repo_s_userId_name':
        'select * from repo_repo where visibly = 0 and user_id = %s and name = %s limit 0, 1',
    'repo_l_userId':
        'select * from repo_repo where visibly = 0 and user_id = %s order by modify_time desc limit %s, %s',
    'repo_c_userId':
        'select 0 as id, count(1) as count from repo_repo where visibly = 0 and user_id = %s',
    # repo_member #
    'repomember_l_repoId':
        'select * from repo_repomember where visibly = 0 and repo_id = %s order by modify_time asc',
    'repomember_s_ruid':
        'select * from repo_repomember where visibly = 0 and repo_id = %s and user_id = %s limit 0, 1',
    # repo_issues #
    'repoissues_l_cons_modify':
        'select * from repo_issues where visibly = 0 and repo_id = %s and assigned = %s and tracker = %s and status = %s and priority = %s order by modify_time desc limit %s, %s',
    'repoissues_l_cons_create':
        'select * from repo_issues where visibly = 0 and repo_id = %s and assigned = %s and tracker = %s and status = %s and priority = %s order by create_time desc limit %s, %s',
    'repoissues_s_id':
        'select * from repo_issues where visibly = 0 and repo_id = %s and id = %s limit 0,1',
    'issuescomment_l_issuesId':
        'select * from repo_issuescomment where visibly = 0 and issues_id = %s order by create_time asc limit %s, %s',
    # repo_forkhistory #
    'forkhistory_l_repoId':
        'select * from repo_forkhistory where repo_id = %s order by modify_time desc limit 0, 50',
    # repo_watchhistory #
    'watchhistory_l_repoId':
        'select * from repo_watchhistory where watch_repo_id = %s order by modify_time desc limit 0, 50',
    # stats #
    'statsrepo_l_cons':
        'select * from stats_statsrepo where statstype = %s and datetype = %s and date between %s and %s and repo_id = %s',
    'statsuser_l_cons':
        'select * from stats_statsuser where statstype = %s and datetype = %s and date between %s and %s and user_id = %s',
    'per_statsrepo_l_cons':
        'select * from stats_statsrepo where statstype = %s and datetype = %s and date = %s and repo_id = %s order by count desc limit 0, 10',
    'per_statsuser_l_cons':
        'select * from stats_statsuser where statstype = %s and datetype = %s and date = %s and user_id = %s order by count desc limit 0, 10',
    'allstatsrepo_l_cons':
        'select * from stats_statsrepo where statstype = %s and datetype = %s and date = %s order by count desc limit %s, %s',
}

def get_many(model, table, pids):
    if len(pids) == 0:
        return []
    ids_key = get_ids_key(table, pids)
    cache_objs_map = cache.get_many(ids_key)
    many_objects = [cache_objs_map[key] for key in cache_objs_map]
    uncache_ids_key = list( set(ids_key) - set(cache_objs_map.keys()) )
    uncache_ids = get_uncache_ids(uncache_ids_key)
    
    if len(uncache_ids) > 0:
        objects = model.objects.filter(id__in=uncache_ids)
        add_many(table, objects)
        many_objects.extend(objects)
    return many_objects

def get(model, table, pid):
    id_key = get_id_key(table, pid)
    obj = cache.get(id_key)
    if obj is not None:
        return obj
    obj = model.objects.get(id = pid, visibly = 0)
    cache.add(id_key, obj)
    return obj

def query(model, table, pt_id, rawsql_id, parameters):
    return model.objects.raw(rawsql[rawsql_id], parameters) 
    if pt_id == None:
        return model.objects.raw(rawsql[rawsql_id], parameters)
    ver_key = get_ver_key(table, pt_id)
    version = cache.get(ver_key)
    if version is not None:
        version = int(time.time()*1000-1334000000000)
        cache.add(ver_key, version)
        ids = []
        for obj in model.objects.raw(rawsql[rawsql_id], parameters):
            ids.append(obj.id)
        lis_key = get_lis_key(version, rawsql_id, parameters)
        cache.add(lis_key, ids)
        ids_key = get_ids_key(table, ids)
        cache_obj_dict = cache.get_many(ids_key)
        un_cache_ids_key = list( set(ids) - set(cache_obj_dict.keys()) )
        un_cache_ids = get_un_cache_ids(un_cache_ids_key)
        objects = model.objects.filter(id__in=un_cache_ids)
        for obj in objects:
            cache.add(get_id_key(table, obj.id), obj)
            cache_obj_dict.add(get_id_key(table, obj.id), obj)
        return [cache_obj_dict.get(get_id_key(table, id)) for id in ids]
    else:
        pass
    return model.objects.raw(rawsql[rawsql_id], parameters)

def queryraw(model, rawsql_id, parameters):
    return model.objects.raw(rawsql[rawsql_id], parameters)
    
def count(model, table, pt_id, rawsql_id, parameters):
    return countraw(rawsql_id, parameters)

def countraw(rawsql_id, parameters):
    count = Count.objects.raw(rawsql[rawsql_id], parameters)[0]
    return count.count

def execute(rawsql_id, parameters):
    cursor = connection.cursor()
    cursor.execute(rawsql[rawsql_id], parameters)
    transaction.commit_unless_managed()

def get_ver_key(table, pt_id):
    return 'ver_%s|%s' % (table, pt_id)

def get_lis_key(version, rawsql_id, parameters):
    p_len = len(parameters) 
    return ('lis_%s|%s' + '|%s'*p_len) % tuple([version, rawsql_id] + parameters)

def get_id_key(table, id):
    return 'id_%s|%s' % (table, id)

def get_ids_key(table, ids):
    return [get_id_key(table, id) for id in ids]

def get_uncache_ids(uncache_ids_key):
    return [key.split('|')[1] for key in uncache_ids_key] 

def add_many(table, objects):
    for sobject in objects: 
        cache.add(get_id_key(table, sobject.id), sobject)
