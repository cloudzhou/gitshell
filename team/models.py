# -*- coding: utf-8 -*-
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

class GroupMember(BaseModel):
    team_user_id = models.IntegerField(default=0, null=False)
    group_id = models.IntegerField(default=0, null=False)
    member_user_id = models.IntegerField(default=0, null=False)

    member_userprofile = None

class RepoPermission(BaseModel):
    repo_id = models.IntegerField(default=0, null=False)
    global_permission = models.IntegerField(default=0, null=False)
    user_permission_set_id = models.IntegerField(default=0, null=False)
    group_permission_set_id = models.IntegerField(default=0, null=False)

    user_permission_set = None
    group_permission_set = None

class BranchPermission(BaseModel):
    repo_id = models.IntegerField(default=0, null=False)
    refname = models.CharField(max_length=64)
    global_permission = models.IntegerField(default=0, null=False)
    user_permission_set_id = models.IntegerField(default=0, null=False)
    group_permission_set_id = models.IntegerField(default=0, null=False)

    user_permission_set = None
    group_permission_set = None

class PermissionItem(BaseModel): 
    team_user_id = models.IntegerField(default=0, null=False)
    set_id = models.IntegerField(default=0, null=False)
    user_id = models.IntegerField(default=0, null=False)
    group_id = models.IntegerField(default=0, null=False)
    permission = models.IntegerField(default=0, null=False)

    team_user = None
    userprofile = None
    group = None
    permission_view = ''

class TeamManager():
    
    # model teamMember
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
        member_userprofile.has_joined_team = 1
        member_userprofile.save()
        exists_teamMember = TeamManager.get_teamMember_by_teamUserId_userId(teamUser.id, member_userprofile.id)
        if exists_teamMember:
            return None
        teamMember = TeamMember(team_user_id = teamUser.id, user_id = member_userprofile.id, group_id = 0, permission = 2, is_admin = 0)
        teamMember.save()
        return teamMember

    @classmethod
    def list_teamMember_by_userId(self, user_id):
        userprofile = GsuserManager.get_userprofile_by_id(user_id)
        if userprofile.has_joined_team == 0:
            return []
        teamMembers = query(TeamMember, None, 'teammember_l_userId', [user_id])
        for x in teamMembers:
            x.user = GsuserManager.get_userprofile_by_id(x.user_id)
            x.team_user = GsuserManager.get_userprofile_by_id(x.team_user_id)
        return teamMembers

    @classmethod
    def list_teamMember_by_teamUserId(self, team_user_id):
        userprofile = GsuserManager.get_userprofile_by_id(team_user_id)
        if userprofile.is_team_account == 0:
            return []
        teamMembers = query(TeamMember, team_user_id, 'teammember_l_teamUserId', [team_user_id])
        for x in teamMembers:
            x.user = GsuserManager.get_userprofile_by_id(x.user_id)
            x.team_user = userprofile
        return teamMembers

    @classmethod
    def get_teamMember_by_teamUserId_userId(self, team_user_id, user_id):
        teamMember = query_first(TeamMember, team_user_id, 'teammember_s_teamUserId_userId', [team_user_id, user_id])
        if not teamMember:
            return None
        teamMember.user = GsuserManager.get_userprofile_by_id(teamMember.user_id)
        teamMember.team_user = GsuserManager.get_userprofile_by_id(teamMember.team_user_id)
        return teamMember

    # model group
    @classmethod
    def get_teamGroup_by_id(self, group_id):
        return get(TeamGroup, group_id)

    @classmethod
    def get_teamGroup_by_teamUserId_name(self, team_user_id, name):
        teamGroup = query_first(TeamGroup, None, 'teamgroup_s_teamUserId_name', [team_user_id, name])
        return teamGroup

    @classmethod
    def list_teamGroup_by_teamUserId(self, team_user_id):
        teamGroups = query(TeamGroup, team_user_id, 'teamgroup_l_teamUserId', [team_user_id])
        return teamGroups

    @classmethod
    def list_groupMember_by_teamGroupId(self, group_id):
        groupMembers = query(GroupMember, group_id, 'groupmember_l_groupId', [group_id])
        user_ids = [x.member_user_id for x in groupMembers]
        userprofiles = GsuserManager.list_userprofile_by_ids(user_ids)
        userprofile_dict = dict((x.id, x)for x in userprofiles)
        for x in groupMembers:
            if x.member_user_id in userprofile_dict:
                x.member_userprofile = userprofile_dict[x.member_user_id]
        return groupMembers

    @classmethod
    def get_groupMember_by_teamGroupId_memberUserId(self, group_id, member_user_id):
        groupMember = query_first(GroupMember, group_id, 'groupmember_s_groupId_memberUserId', [group_id, member_user_id])
        if not groupMember:
            return None
        groupMember.member_userprofile = GsuserManager.get_userprofile_by_id(groupMember.member_user_id)
        return groupMember

    # permission
    @classmethod
    def get_repoPermission_by_repoId(self, repo_id):
        repoPermission = query_first(RepoPermission, repo_id, 'repopermission_s_repoId', [repo_id])
        if not repoPermission:
            return None
        user_permission_set = self.list_permissionItem_by_setId(repoPermission.user_permission_set_id)
        group_permission_set = self.list_permissionItem_by_setId(repoPermission.group_permission_set_id)
        repoPermission.user_permission_set = user_permission_set
        repoPermission.group_permission_set = group_permission_set
        return repoPermission

    @classmethod
    def get_branchPermission_by_repoId_refname(self, repo_id, refname):
        branchPermission = query_first(BranchPermission, repo_id, 'branchpermission_s_repoId_refname', [repo_id, refname])
        if not branchPermission:
            return None
        user_permission_set = self.list_permissionItem_by_setId(repoPermission.user_permission_set_id)
        group_permission_set = self.list_permissionItem_by_setId(repoPermission.group_permission_set_id)
        repoPermission.user_permission_set = user_permission_set
        repoPermission.group_permission_set = group_permission_set
        return branchPermission

    #TODO limit user
    @classmethod
    def list_permissionItem_by_setId(self, set_id):
        branchPermissions = query(PermissionItem, set_id, 'permissionitem_l_setId', [set_id])
        if len(branchPermissions) == 0:
            return []
        userprofile_ids = [x.user_id for x in branchPermissions]
        userprofiles = GsuserManager.list_userprofile_by_ids(userprofile_ids)
        userprofile_dict = dict((x.id, x)for x in userprofiles)

        teamGroup_dict = {}
        for x in branchPermissions:
            if x.group_id in teamGroup_dict:
                continue
            teamGroup = TeamMember.list_teamGroup_by_id(x.group_id)
            if not teamGroup:
                continue
            teamGroup_dict[teamGroup.id] = teamGroup

        filtered_branchPermissions = []
        for branchPermission in branchPermissions:
            if branchPermission.user_id not in userprofile_dict and branchPermission.group_id not in teamGroup_dict:
                branchPermission.visibly = 1
                branchPermission.save()
                continue
            if branchPermission.user_id in userprofile_dict:
                branchPermission.userprofile = userprofile_dict[branchPermission.user_id]
            if branchPermission.group_id in teamGroup_dict:
                branchPermission.group = teamGroup_dict[branchPermission.group_id]
            if branchPermission.permission in PERMISSION.VIEW:
                branchPermission.permission_view = PERMISSION.VIEW[branchPermission.permission]
            filtered_branchPermissions.append(branchPermission)

        return filtered_branchPermissions

    def set_repo_global_permission(repo_id, permission):
        pass

    def set_repo_user_permission(repo_id, user_id, permission):
        pass

    def set_repo_group_permission(repo_id, group_id, permission):
        pass

    def set_branch_global_permission(repo_id, refname, permission):
        pass

    def set_branch_user_permission(repo_id, refname, user_id, permission):
        pass

    def set_branch_group_permission(repo_id, refname, group_id, permission):
        pass

    def remove_permission_item(team_user_id, id):
        pass

    # other
    @classmethod
    def get_current_user(self, user, userprofile):
        current_user_id = userprofile.current_user_id
        if current_user_id != 0 and current_user_id != userprofile.id:
            teamMember = TeamManager.get_teamMember_by_teamUserId_userId(current_user_id, userprofile.id)
            if teamMember:
                current_user = GsuserManager.get_user_by_id(current_user_id)
                if current_user:
                    return current_user
        return user

class PERMISSION:

    NONE = -1
    DEFAULT = 0
    PULL = 1
    PUSH = 2
    ADMIN = 3

    VIEW = {
        -1: u'没有任何权限',
        0: u'默认权限',
        1: u'只读权限(pull)',
        2: u'读写权限(pull+push)',
        3: u'管理权限(admin)',
    }

