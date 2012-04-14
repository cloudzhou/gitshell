from django.db import models
from gitshell.objectscache.da import query

class UserPubkey(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)

    user_id = models.IntegerField(null=False)
    name = models.CharField(max_length=32, null=False)
    key = models.CharField(max_length=1024,  null=False)
    fingerprint = models.CharField(max_length=64, db_index=True, null=False)

class KeyauthManager():

    @classmethod
    def list_userPubkey_by_user_id(self, user_id):
        return query(UserPubkey, 'keyauth_userpubkey', user_id, 'userpubkey_user_id', [user_id])
