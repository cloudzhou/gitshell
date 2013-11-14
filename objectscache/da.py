# -*- coding: utf-8 -*-  
import base64
from django.core.cache import cache
from django.db import connection, transaction
from gitshell.objectscache.models import Count
from gitshell.settings import logger
from django.db.models.signals import post_save, post_delete
import time

# table field partitioning #
table_ptkey_field = {
    'auth_user': 'id',
    'gsuser_recommend': 'user_id',
    'gsuser_userprofile': 'id',
    'keyauth_userpubkey': 'user_id',
    'keyvalue_keyvalue': 'user_id',
    'repo_repo': 'user_id',
    'repo_repomember': 'repo_id',
    'repo_star': 'user_id',
    'repo_commithistory': 'repo_id',
    'repo_forkhistory': 'repo_id',
    'repo_watchhistory': 'user_id',
    'repo_pullrequest': 'desc_repo_id',
    'repo_webhookurl': 'repo_id',
    'issue_issue': 'repo_id',
    'issue_issuecomment': 'issue_id',
    'stats_statsrepo': 'repo_id',
    'stats_statsuser': 'user_id',
    'todolist_scene': 'user_id',
    'todolist_todolist': 'user_id',
    'gsuser_thirdpartyuser': 'user_type',
    'gsuser_useremail': 'user_id',
    'feed_notifmessage': 'to_user_id',
    'feed_notifsetting': 'user_id',
    'team_teammember': 'user_id',
}
rawsql = {
    # userpubkey #
    'userpubkey_l_userId':
        'select * from keyauth_userpubkey where visibly = 0 and user_id = %s limit 0, 10',
    'userpubkey_l_fingerprint':
        'select * from keyauth_userpubkey where visibly = 0 and fingerprint = %s limit 0, 10',
    'userpubkey_c_fingerprint':
        'select 0 as id, count(1) as count from keyauth_userpubkey where visibly = 0 and fingerprint = %s limit 0, 10',
    'userpubkey_s_id':
        'select * from keyauth_userpubkey where visibly = 0 and user_id = %s and id = %s limit 0, 1',
    'userpubkey_s_fingerprint':
        'select * from keyauth_userpubkey where visibly = 0 and fingerprint = %s limit 0, 1',
    'userpubkey_s_userId_fingerprint':
        'select * from keyauth_userpubkey where visibly = 0 and user_id = %s and fingerprint = %s limit 0, 1',
    # user #
    'recommend_l_userId':
        'select * from gsuser_recommend where visibly = 0 and user_id = %s order by modify_time desc limit %s, %s',
    'thirdpartyuser_s_userType_tpId':
        'select * from gsuser_thirdpartyuser where visibly = 0 and user_type = %s and tp_id = %s',
    'useremail_l_userId':
        'select * from gsuser_useremail where visibly = 0 and user_id = %s order by create_time limit 100',
    'useremail_s_userId_email':
        'select * from gsuser_useremail where visibly = 0 and user_id = %s and email = %s limit 0, 1',
    # repo #
    'repo_s_userId_name':
        'select * from repo_repo where visibly = 0 and user_id = %s and name = %s limit 0, 1',
    'repo_l_userId':
        'select * from repo_repo where visibly = 0 and user_id = %s order by modify_time desc limit %s, %s',
    'repo_l_unprivate_userId':
        'select * from repo_repo where visibly = 0 and user_id = %s and auth_type != 2 order by modify_time desc limit %s, %s',
    'repo_c_userId':
        'select 0 as id, count(1) as count from repo_repo where visibly = 0 and user_id = %s',
    'repo_l_forkRepoId':
        'select * from repo_repo where visibly = 0 and fork_repo_id = %s order by modify_time desc limit 0, 100',
    'repo_s_userId_forkrepoId':
        'select * from repo_repo where visibly = 0 and user_id = %s and fork_repo_id = %s limit 0, 1',
    # repo_commithistory #
    'commithistory_l_repoId_pushrevrefId':
        'select * from repo_commithistory where visibly = 0 and repo_id = %s and pushrevref_id = %s order by modify_time desc limit %s, %s',
    # repo_pullrequest #
    'pullrequest_l_descRepoId':
        'select * from repo_pullrequest where visibly = 0 and desc_repo_id = %s order by status, modify_time desc limit %s, %s',
    'pullrequest_l_pullUserId':
        'select * from repo_pullrequest where visibly = 0 and pull_user_id = %s order by status, modify_time desc limit %s, %s',
    'pullrequest_l_mergeUserId':
        'select * from repo_pullrequest where visibly = 0 and merge_user_id = %s order by status, modify_time desc limit %s, %s',
    'pullrequest_l_descUserId_pullUserId':
        'select * from repo_pullrequest where visibly = 0 and desc_user_id = %s and pull_user_id = %s order by status, modify_time desc limit %s, %s',
    'pullrequest_l_descUserId_mergeUserId':
        'select * from repo_pullrequest where visibly = 0 and desc_user_id = %s and merge_user_id = %s order by status, modify_time desc limit %s, %s',
    'pullrequest_c_descRepoId':
        'select 0 as id, count(1) as count from repo_pullrequest where visibly = 0 and desc_repo_id = %s and status = %s',
    'pullrequest_c_pullUserId':
        'select 0 as id, count(1) as count from repo_pullrequest where visibly = 0 and pull_user_id = %s and status = %s',
    'pullrequest_c_mergeUserId':
        'select 0 as id, count(1) as count from repo_pullrequest where visibly = 0 and merge_user_id = %s and status = %s',
    # repo_member #
    'repomember_l_repoId':
        'select * from repo_repomember where visibly = 0 and repo_id = %s order by modify_time asc',
    'repomember_s_ruid':
        'select * from repo_repomember where visibly = 0 and repo_id = %s and user_id = %s limit 0, 1',
    'repomember_l_userId':
        'select * from repo_repomember where visibly = 0 and user_id = %s order by modify_time desc limit %s, %s',
    # repo_repo #
    'repo_l_last_push_time':
        'select * from repo_repo where last_push_time >= %s limit 0, 5000',
    # repo_forkhistory #
    'forkhistory_l_repoId':
        'select * from repo_forkhistory where visibly = 0 and repo_id = %s order by modify_time desc limit 0, 50',
    # repo_watchhistory #
    'watchhistory_l_repoId':
        'select * from repo_watchhistory where visibly = 0 and watch_repo_id = %s order by modify_time desc limit 0, 50',
    'watchhistory_s_user':
        'select * from repo_watchhistory where visibly = 0 and user_id = %s and watch_user_id = %s limit 0, 1',
    'watchhistory_s_repo':
        'select * from repo_watchhistory where visibly = 0 and user_id = %s and watch_repo_id = %s limit 0, 1',
    # repo_star #
    'star_l_userId':
        'select * from repo_star where visibly = 0 and user_id = %s order by modify_time desc limit %s, %s',
    'star_l_repoId':
        'select * from repo_star where visibly = 0 and star_repo_id = %s order by modify_time desc limit %s, %s',
    'star_s_user':
        'select * from repo_star where visibly = 0 and user_id = %s and star_user_id = %s limit 0, 1',
    'star_s_repo':
        'select * from repo_star where visibly = 0 and user_id = %s and star_repo_id = %s limit 0, 1',
    # repo_webhookurl #
    'webhookurl_l_repoId':
        'select * from repo_webhookurl where visibly = 0 and repo_id = %s order by status asc, modify_time desc limit %s, %s',
    # issue_issue #
    'issue_l_cons_modify':
        'select * from issue_issue where visibly = 0 and repo_id = %s order by modify_time desc limit %s, %s',
    'issue_l_cons_create':
        'select * from issue_issue where visibly = 0 and repo_id = %s order by create_time desc limit %s, %s',
    'issue_l_assigned_modify':
        'select * from issue_issue where visibly = 0 and assigned = %s order by status, modify_time desc limit %s, %s',
    'issue_l_assigned_create':
        'select * from issue_issue where visibly = 0 and assigned = %s order by status, create_time desc limit %s, %s',
    'issue_l_userId_assigned_modify':
        'select * from issue_issue where visibly = 0 and user_id = %s and assigned = %s order by status, modify_time desc limit %s, %s',
    'issue_l_userId_assigned_create':
        'select * from issue_issue where visibly = 0 and user_id = %s and assigned = %s order by status, create_time desc limit %s, %s',
    'issue_s_id':
        'select * from issue_issue where visibly = 0 and repo_id = %s and id = %s limit 0,1',
    'issuecomment_l_issueId':
        'select * from issue_issuecomment where visibly = 0 and issue_id = %s order by create_time asc limit %s, %s',
    # stats #
    'statsrepo_s_hash_id':
        'select * from stats_statsrepo where repo_id = %s and hash_id = %s limit 0, 1',
    'statsuser_s_hash_id':
        'select * from stats_statsuser where user_id = %s and hash_id = %s limit 0, 1',
    'statsrepo_l_cons':
        'select * from stats_statsrepo where repo_id = %s and statstype = %s and datetype = %s and date between %s and %s',
    'statsuser_l_cons':
        'select * from stats_statsuser where user_id = %s and statstype = %s and datetype = %s and date between %s and %s',
    'per_statsrepo_l_cons':
        'select * from stats_statsrepo where repo_id = %s and statstype = %s and datetype = %s and date = %s order by count desc limit 0, 10',
    'per_statsuser_l_cons':
        'select * from stats_statsuser where user_id = %s and statstype = %s and datetype = %s and date = %s order by count desc limit 0, 10',
    'allstatsrepo_l_cons':
        'select * from stats_statsrepo where statstype = %s and datetype = %s and date = %s order by count desc limit %s, %s',
    # todolist #
    'todolist_l_userId_sceneId':
        'select * from todolist_todolist where visibly = 0 and user_id = %s and scene_id = %s and is_done = %s order by modify_time desc limit %s, %s',
    'todolist_s_userId_id':
        'select * from todolist_todolist where visibly = 0 and user_id = %s and id = %s',
    'scene_l_userId':
        'select * from todolist_scene where visibly = 0 and user_id = %s order by modify_time desc limit %s, %s',
    'scene_l_userId_id':
        'select * from todolist_scene where visibly = 0 and user_id = %s and id = %s',
    'scene_l_userId_name':
        'select * from todolist_scene where visibly = 0 and user_id = %s and name = %s',
    # feed #
    'notifmessage_l_toUserId':
        'select * from feed_notifmessage where visibly = 0 and to_user_id = %s order by modify_time desc limit %s, %s',
    'notifmessage_l_toUserId_userId':
        'select * from feed_notifmessage where visibly = 0 and to_user_id = %s and user_id = %s order by modify_time desc limit %s, %s',
    'notifmessage_l_toUserId_modifyTime':
        'select * from feed_notifmessage where visibly = 0 and to_user_id = %s and modify_time > %s and modify_time <= %s order by modify_time desc limit %s, %s',
    'notifmessage_s_toUserId_notifType_relativeId':
        'select * from feed_notifmessage where visibly = 0 and to_user_id = %s and notif_type = %s and relative_id = %s limit 0, 1',
    'notifsetting_l_expectNotifTime':
        'select * from feed_notifsetting where visibly = 0 and expect_notif_time <= %s and notif_fqcy > 0 limit %s, %s',
    'notifsetting_s_userId':
        'select * from feed_notifsetting where visibly = 0 and user_id = %s limit 0, 1',
    # team #
    'teammember_s_userId_teamUserId':
        'select * from team_teammember where visibly = 0 and user_id = %s and team_user_id = %s limit 0, 1',
    'teammember_l_userId':
        'select * from team_teammember where visibly = 0 and user_id = %s order by modify_time desc limit 0, 1000',
    'teammember_l_teamUserId':
        'select * from team_teammember where visibly = 0 and team_user_id = %s order by is_admin desc, modify_time desc limit 0, 1000',
}

def get(model, pkid):
    return __get(model, pkid, True)

def get_raw(model, pkid):
    return __get(model, pkid, False)

def __get(model, pkid, only_visibly):
    table = model._meta.db_table
    id_key = __get_idkey(table, pkid)
    obj = cache.get(id_key)
    if obj is not None:
        return obj
    try:
        if only_visibly and hasattr(model, 'visibly'):
            obj = model.objects.get(visibly = 0, id = pkid)
        else:
            obj = model.objects.get(id = pkid)
        cache.add(id_key, obj)
        return obj
    except Exception, e:
        logger.exception(e)
    return None

def get_many(model, pkids):
    return __get_many(model, pkids, True)

def get_raw_many(model, pkids):
    return __get_many(model, pkids, False)

def __get_many(model, pkids, only_visibly):
    table = model._meta.db_table
    if len(pkids) == 0:
        return []
    ids_key = __get_idskey(table, pkids)
    cache_objs_map = cache.get_many(ids_key)
    many_objects = [cache_objs_map[key] for key in cache_objs_map]
    uncache_ids_key = list( set(ids_key) - set(cache_objs_map.keys()) )
    uncache_ids = __get_uncache_ids(uncache_ids_key)
    
    if len(uncache_ids) > 0:
        objects = []
        try:
            if only_visibly and hasattr(model, 'visibly'):
                objects = model.objects.filter(visibly=0).filter(id__in=uncache_ids)
            else:
                objects = model.objects.filter(id__in=uncache_ids)
        except Exception, e:
            logger.exception(e)
        __add_many(table, objects)
        many_objects.extend(objects)
    objects_map = dict([(x.id, x) for x in many_objects])
    order_many_objects = []
    for pkid in pkids:
        if pkid in objects_map:
            order_many_objects.append(objects_map[pkid])
    return order_many_objects

def query(model, pt_id, rawsql_id, parameters):
    table = model._meta.db_table
    if pt_id is None:
        return queryraw(model, rawsql_id, parameters)
    version = __get_version(table, pt_id)
    sqlkey = __get_sqlkey(version, rawsql_id, parameters)
    value = cache.get(sqlkey)
    if value is None:
        value = []
        objects = queryraw(model, rawsql_id, parameters)
        for obj in objects:
            value.append(obj.id)
            id_key = __get_idkey(table, obj.id)
            cache.add(id_key, obj)
        cache.add(sqlkey, value)
    return get_many(model, value)

def query_first(model, pt_id, rawsql_id, parameters):
    objects = query(model, pt_id, rawsql_id, parameters)
    if len(objects) > 0:
        return objects[0]
    return None

def queryraw(model, rawsql_id, parameters):
    try:
        return list(model.objects.raw(rawsql[rawsql_id], parameters))
    except Exception, e:
        logger.exception(e)
    return []
    
def count(model, pt_id, rawsql_id, parameters):
    table = model._meta.db_table
    if pt_id is not None:
        version = __get_version(table, pt_id)
        sqlkey = __get_sqlkey(version, rawsql_id, parameters)
        value = cache.get(sqlkey)
        if value is not None:
            return value
        value = countraw(rawsql_id, parameters)
        cache.add(sqlkey, value)
        return value
    return countraw(rawsql_id, parameters)

def countraw(rawsql_id, parameters):
    count = Count.objects.raw(rawsql[rawsql_id], parameters)[0]
    return count.count

def execute(rawsql_id, parameters):
    cursor = connection.cursor()
    cursor.execute(rawsql[rawsql_id], parameters)
    transaction.commit_unless_managed()

def da_post_save(mobject):
    table = mobject._meta.db_table
    if not hasattr(mobject, 'id'):
        return False
    id_key = __get_idkey(table, mobject.id)
    cache.delete(id_key)
    if table in table_ptkey_field:
        ptkey_field = table_ptkey_field[table]
        ptkey_value = getattr(mobject, ptkey_field)
        version = __get_current_version()
        cache.set(__get_verkey(table, ptkey_value), version)
    return True

def get_version(model, pt_id):
    table = model._meta.db_table
    return __get_version(table, pt_id)

def get_sqlkey(version, rawsql_id, parameters):
    return __get_sqlkey(version, rawsql_id, parameters)

def __get_version(table, pt_id):
    verkey = __get_verkey(table, pt_id)
    version = cache.get(verkey)
    if version is not None:
        return version
    version = __get_current_version()
    cache.set(verkey, version)
    return version

def __get_verkey(table, pt_id):
    return 'ver_%s|%s' % (table, pt_id)

def __get_sqlkey(version, rawsql_id, parameters):
    filter_parameters = [base64.b64encode(x.encode('utf-8')) if isinstance(x, unicode) else base64.b64encode(str(x)) for x in parameters]
    p_len = len(filter_parameters) 
    return ('lis_%s|%s' + '|%s'*p_len) % tuple([version, rawsql_id] + filter_parameters)

def __get_idkey(table, id):
    return 'id_%s|%s' % (table, id)

def __get_idskey(table, ids):
    return [__get_idkey(table, id) for id in ids]

def __get_uncache_ids(uncache_ids_key):
    return [key.split('|')[1] for key in uncache_ids_key] 

def __add_many(table, objects):
    for sobject in objects: 
        cache.add(__get_idkey(table, sobject.id), sobject)

def __get_current_version():
    return int(time.time()*1000-1334000000000)
    
