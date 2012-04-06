from django.db import models
import os

class UserPubkey(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)

    user_id = models.IntegerField(null=False)
    pubkey_name = models.CharField(max_length=32, null=False)
    pub_key = models.CharField(max_length=1024,  null=False)
    key_fingerprint = models.CharField(max_length=64, db_index=True, null=False)
    is_active = models.SmallIntegerField(default=0, null=False) 
