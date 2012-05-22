from django.db import models
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, queryraw, execute, count

class UserPubkey(BaseModel):
    user_id = models.IntegerField(null=False)
    name = models.CharField(max_length=32, null=False)
    key = models.CharField(max_length=1024,  null=False)
    fingerprint = models.CharField(max_length=64, db_index=True, null=False)

class KeyauthManager():

    @classmethod
    def list_userpubkey_by_userId(self, user_id):
        return query(UserPubkey, 'keyauth_userpubkey', user_id, 'userpubkey_l_userId', [user_id])

    @classmethod
    def get_userpubkey_by_userId_fingerprint(self, user_id, fingerprint):
        userPubkeys = query(UserPubkey, 'keyauth_userpubkey', user_id, 'userpubkey_s_userId_fingerprint', [user_id, fingerprint])
        if len(list(userPubkeys)) > 0:
            return userPubkeys[0]
        return None

    @classmethod
    def update_userpubkey_by_id(self, id):
        return execute('userpubkey_u_id', [id])

    @classmethod
    def count_userpubkey_by_fingerprint(self, fingerprint):
        return count('userpubkey_c_fingerprint', [fingerprint])

    @classmethod
    def get_userpubkey_by_fingerprint(self, fingerprint):
        userPubkeys = queryraw(UserPubkey, 'userpubkey_s_fingerprint', [fingerprint])
        if len(list(userPubkeys)) > 0:
            return userPubkeys[0]
        return None
