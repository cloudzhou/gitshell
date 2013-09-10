import time
from django.db import models
from django.contrib.auth.models import User, UserManager
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, query_first, get, get_many, execute, count, countraw

class TeamMember(BaseModel):
    team_user_id = models.IntegerField(default=0, null=False)
    user_id = models.IntegerField(default=0, null=False)
    group_id = models.IntegerField(default=0, null=False)
    permission = models.IntegerField(default=0, null=False)
    is_admin = models.IntegerField(default=0, null=False)

    def has_admin_rights(self):
        return self.is_admin == 1
    def has_read_rights(self):
        return self.permission == 1 or self.permission == 2
    def has_write_rights(self):
        return self.permission == 2

class TeamGroup(BaseModel):
    team_user_id = models.IntegerField(default=0, null=False)
    name = models.CharField(max_length=512, null=True)
    desc = models.CharField(max_length=1024, null=True)
    permission = models.IntegerField(default=0, null=False)
    is_admin = models.IntegerField(default=0, null=False)

    def has_admin_rights(self):
        return self.is_admin == 1
    def has_read_rights(self):
        return self.permission == 1 or self.permission == 2
    def has_write_rights(self):
        return self.permission == 2

