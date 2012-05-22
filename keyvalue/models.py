from django.db import models
from gitshell.objectscache.models import BaseModel

# common key value
class Keyvalue(BaseModel):
    key_type = models.IntegerField(null=False)
    user_id = models.IntegerField(null=False)
    key_name = models.CharField(max_length=16,  null=False)
    key_value = models.CharField(max_length=2048,  null=False)

# note
# create index for (key_type, user_id, key_name)
