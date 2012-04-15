# -*- coding: utf-8 -*-  
from django.core.cache import cache
from django.db import connection, transaction
from gitshell.objectscache.models import Count
import time

rawsql = {
    'userpubkey_by_user_id':
        'SELECT * FROM keyauth_userpubkey WHERE user_id = %s and visibly = 0 limit 0, 10',
    'userpubkey_by_id':
        'UPDATE keyauth_userpubkey SET visibly = 1 WHERE id = %s',
    'userpubkey_by_fingerprint':
        'SELECT 0 as id, count(1) as count FROM keyauth_userpubkey WHERE fingerprint = %s and visibly = 0 limit 0, 10',
}

def get_many(model, table, pids):
    pass

def get(model, table, pid):
    id_key = get_id_key(table, pid)
    obj = cache.get(id_key)
    if obj is not None:
        return obj
    obj = model.objects.get(id = pid)
    cache.add(id_key, obj)
    return obj

def query(model, table, pt_id, rawsql_id, parameters):
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

def count(rawsql_id, parameters):
    count = Count.objects.raw(rawsql[rawsql_id], [parameters])[0]
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

def get_un_cache_ids(un_cache_ids_key):
    return [key.split('|')[1] for key in un_cache_ids_key] 

