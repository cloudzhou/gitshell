from django.db import models

# common key value
class Keyvalue(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)

    key_type = models.IntegerField(null=False)
    user_id = models.IntegerField(null=False)
    key_name = models.CharField(max_length=16,  null=False)
    key_value = models.CharField(max_length=1024,  null=False)

# note
# create index for (key_type, user_id, key_name)
