import time
from django.db import models
from django.contrib.auth.models import User, UserManager
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, query_first, get, get_many, execute, count, countraw
from gitshell.gsuser.models import GsuserManager

class TeamMember(BaseModel):
    team_user_id = models.IntegerField(default=0, null=False)
    user_id = models.IntegerField(default=0, null=False)
    group_id = models.IntegerField(default=0, null=False)
    permission = models.IntegerField(default=0, null=False)
    is_admin = models.IntegerField(default=0, null=False)

    team_user = None

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

class TeamManager():
    
    @classmethod
    def get_teamMember_by_id(self, id):
        return get(TeamMember, id)

    @classmethod
    def is_teamMember(self, team_user_id, user_id):
        teamMembers = self.list_teamMember_by_teamUserId(team_user_id)
        for teamMember in teamMembers:
            if teamMember.user_id == user_id:
                return True
        return False

    @classmethod
    def add_teamMember_by_email(self, teamUser, email):
        member_userprofile = GsuserManager.get_userprofile_by_email(email)
        return self.add_teamMember_by_userprofile(teamUser, member_userprofile)

    @classmethod
    def add_teamMember_by_username(self, teamUser, username):
        member_userprofile = GsuserManager.get_userprofile_by_name(username)
        return self.add_teamMember_by_userprofile(teamUser, member_userprofile)

    @classmethod
    def add_teamMember_by_userprofile(self, teamUser, member_userprofile):
        if not teamUser or not member_userprofile or member_userprofile.is_team_account == 1:
            return None
        member_userprofile.is_join_team = 1
        member_userprofile.save()
        exists_teamMember = TeamManager.get_teamMember_by_userId_teamUserId(member_userprofile.id, teamUser.id)
        if exists_teamMember:
            return None
        teamMember = TeamMember(team_user_id = teamUser.id, user_id = member_user.id, group_id = 0, permission = 2, is_admin = 0)
        teamMember.save()
        return teamMember

    @classmethod
    def get_teamMember_by_userId_teamUserId(self, user_id, team_user_id):
        teamMember = query_first(TeamMember, user_id, 'teammember_s_userId_teamUserId', [user_id, team_user_id])
        if not teamMember:
            return None
        teamMember.user = GsuserManager.get_userprofile_by_id(teamMember.user_id)
        teamMember.team_user = GsuserManager.get_userprofile_by_id(teamMember.team_user_id)
        return teamMember

    @classmethod
    def list_teamMember_by_userId(self, user_id):
        userprofile = GsuserManager.get_userprofile_by_id(user_id)
        #if userprofile.is_join_team == 0:
        #    return []
        teamMembers = query(TeamMember, user_id, 'teammember_l_userId', [user_id])
        for x in teamMembers:
            x.user = GsuserManager.get_userprofile_by_id(x.user_id)
            x.team_user = GsuserManager.get_userprofile_by_id(x.team_user_id)
        return teamMembers

    @classmethod
    def list_teamMember_by_teamUserId(self, team_user_id):
        userprofile = GsuserManager.get_userprofile_by_id(team_user_id)
        if userprofile.is_team_account == 0:
            return []
        teamMembers = query(TeamMember, None, 'teammember_l_teamUserId', [team_user_id])
        for x in teamMembers:
            x.user = GsuserManager.get_userprofile_by_id(x.user_id)
            x.team_user = userprofile
        return teamMembers

    @classmethod
    def get_current_user(self, user, userprofile):
        current_user_id = userprofile.current_user_id
        if current_user_id != 0 and current_user_id != userprofile.id:
            teamMember = TeamManager.get_teamMember_by_userId_teamUserId(userprofile.id, current_user_id)
            if teamMember:
                current_user = GsuserManager.get_user_by_id(current_user_id)
                if current_user:
                    return current_user
        return user

