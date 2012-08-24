from django.db import models
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, queryraw, execute, count, countraw

class UserPubkey(BaseModel):
    user_id = models.IntegerField(null=False)
    name = models.CharField(max_length=32, null=False)
    key = models.CharField(max_length=1024,  null=False)
    fingerprint = models.CharField(max_length=64, db_index=True, null=False)

class KeyauthManager():

    @classmethod
    def list_userpubkey_by_userId(self, user_id):
        userPubkeys = query(UserPubkey, user_id, 'userpubkey_l_userId', [user_id])
        return userPubkeys

    @classmethod
    def list_userpubkey_by_fingerprint(self, fingerprint):
        userPubkeys = queryraw(UserPubkey, 'userpubkey_l_fingerprint', [fingerprint])
        return userPubkeys

    @classmethod
    def get_userpubkey_by_id(self, user_id, pid):
        userPubkeys = query(UserPubkey, user_id, 'userpubkey_s_id', [user_id, pid])
        if len(userPubkeys) > 0:
            return userPubkeys[0]
        return None

    @classmethod
    def get_userpubkey_by_userId_fingerprint(self, user_id, fingerprint):
        userPubkeys = query(UserPubkey, user_id, 'userpubkey_s_userId_fingerprint', [user_id, fingerprint])
        if len(userPubkeys) > 0:
            return userPubkeys[0]
        return None

    @classmethod
    def count_userpubkey_by_fingerprint(self, fingerprint):
        return countraw('userpubkey_c_fingerprint', [fingerprint])

    @classmethod
    def get_userpubkey_by_fingerprint(self, fingerprint):
        userPubkeys = queryraw(UserPubkey, 'userpubkey_s_fingerprint', [fingerprint])
        if len(userPubkeys) > 0:
            return userPubkeys[0]
        return None

