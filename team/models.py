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
    repo_id = models.IntegerField(default=0, null=False)
    set_id = models.IntegerField(default=0, null=False)
    user_id = models.IntegerField(default=0, null=False)
    group_id = models.IntegerField(default=0, null=False)
    permission = models.IntegerField(default=0, null=False)

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
        teamMember = self.get_teamMember_by_teamUserId_userId(team_user_id, user_id)
        return teamMember is not None

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
        teamGroup = query_first(TeamGroup, team_user_id, 'teamgroup_s_teamUserId_name', [team_user_id, name])
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
        user_permission_set = self.list_permissionItem_by_setId(repoPermission.user_permission_set_id, repo_id)
        group_permission_set = self.list_permissionItem_by_setId(repoPermission.group_permission_set_id, repo_id)
        repoPermission.user_permission_set = user_permission_set
        repoPermission.group_permission_set = group_permission_set
        return repoPermission

    @classmethod
    def list_branchPermission_by_repoId(self, repo_id):
        branchPermissions = query(BranchPermission, repo_id, 'branchpermission_l_repoId', [repo_id])
        return branchPermissions

    @classmethod
    def get_branchPermission_by_repoId_refname(self, repo_id, refname):
        branchPermission = query_first(BranchPermission, repo_id, 'branchpermission_s_repoId_refname', [repo_id, refname])
        if not branchPermission:
            return None
        user_permission_set = self.list_permissionItem_by_setId(repoPermission.user_permission_set_id, repo_id)
        group_permission_set = self.list_permissionItem_by_setId(repoPermission.group_permission_set_id, repo_id)
        repoPermission.user_permission_set = user_permission_set
        repoPermission.group_permission_set = group_permission_set
        return branchPermission

    @classmethod
    def list_permissionItem_by_setId(self, set_id, repo_id):
        permissionItems = query(PermissionItem, set_id, 'permissionitem_l_setId', [set_id])
        if len(permissionItems) == 0:
            return []
        from gitshell.repo.models import Repo, RepoManager
        userprofile_dict = dict((x.id, x)for x in RepoManager.list_repo_team_memberUser(repo_id))

        teamGroup_dict = {}
        for x in permissionItems:
            if x.group_id in teamGroup_dict:
                continue
            teamGroup = self.get_teamGroup_by_id(x.group_id)
            if not teamGroup:
                continue
            teamGroup_dict[teamGroup.id] = teamGroup

        filtered_permissionItems = []
        for permissionItem in permissionItems:
            if permissionItem.user_id not in userprofile_dict and permissionItem.group_id not in teamGroup_dict:
                permissionItem.visibly = 1
                permissionItem.save()
                continue
            if permissionItem.user_id in userprofile_dict:
                permissionItem.userprofile = userprofile_dict[permissionItem.user_id]
            if permissionItem.group_id in teamGroup_dict:
                permissionItem.group = teamGroup_dict[permissionItem.group_id]
            if permissionItem.permission in PERMISSION.VIEW:
                permissionItem.permission_view = PERMISSION.VIEW[permissionItem.permission]
            filtered_permissionItems.append(permissionItem)

        return filtered_permissionItems

    @classmethod
    def get_permissionItem_by_setId_userId(self, set_id, user_id):
        if set_id == 0:
            return None
        permissionItem = query_first(PermissionItem, set_id, 'permissionitem_s_setId_userId', [set_id, user_id])
        if not permissionItem:
            return None
        permissionItem.userprofile = GsuserManager.get_userprofile_by_id(permissionItem.user_id)
        if permissionItem.permission in PERMISSION.VIEW:
            permissionItem.permission_view = PERMISSION.VIEW[permissionItem.permission]
        return permissionItem

    @classmethod
    def get_permissionItem_by_setId_groupId(self, set_id, group_id):
        if set_id == 0:
            return None
        permissionItem = query_first(PermissionItem, set_id, 'permissionitem_s_setId_groupId', [set_id, group_id])
        if not permissionItem:
            return None
        permissionItem.group = self.get_teamGroup_by_id(group_id)
        if permissionItem.permission in PERMISSION.VIEW:
            permissionItem.permission_view = PERMISSION.VIEW[permissionItem.permission]
        return permissionItem

    @classmethod
    def grant_repo_global_permission(self, repo_id, permission):
        if permission not in PERMISSION.VIEW:
            return None
        repoPermission = self.get_repoPermission_by_repoId(repo_id)
        if not repoPermission:
            repoPermission = RepoPermission(repo_id=repo_id)
        repoPermission.global_permission = permission
        repoPermission.save()
        return repoPermission

    @classmethod
    def grant_repo_user_permission(self, repo_id, user_id, permission):
        if permission not in PERMISSION.VIEW:
            return None
        repoPermission = self.get_repoPermission_by_repoId(repo_id)
        if not repoPermission:
            repoPermission = RepoPermission(repo_id=repo_id)
            repoPermission.save()
        user_permission_set_id = repoPermission.user_permission_set_id
        permissionItem = self.get_permissionItem_by_setId_userId(user_permission_set_id, user_id)
        if not permissionItem:
            if user_permission_set_id == 0:
                permissionItem = PermissionItem(repo_id=repo_id, user_id=user_id, permission=permission)
                permissionItem.save()
                permissionItem.set_id = permissionItem.id
                repoPermission.user_permission_set_id = permissionItem.set_id
                repoPermission.save()
            else:
                permissionItem = PermissionItem(repo_id=repo_id, set_id=user_permission_set_id, user_id=user_id, permission=permission)
        permissionItem.permission = permission
        permissionItem.save()
        return permissionItem

    @classmethod
    def grant_repo_group_permission(self, repo_id, group_id, permission):
        if permission not in PERMISSION.VIEW:
            return None
        repoPermission = self.get_repoPermission_by_repoId(repo_id)
        if not repoPermission:
            repoPermission = RepoPermission(repo_id=repo_id)
            repoPermission.save()
        group_permission_set_id = repoPermission.group_permission_set_id
        permissionItem = self.get_permissionItem_by_setId_groupId(group_permission_set_id, group_id)
        if not permissionItem:
            if group_permission_set_id == 0:
                permissionItem = PermissionItem(repo_id=repo_id, group_id=group_id, permission=permission)
                permissionItem.save()
                permissionItem.set_id = permissionItem.id
                repoPermission.group_permission_set_id = permissionItem.set_id
                repoPermission.save()
            else:
                permissionItem = PermissionItem(repo_id=repo_id, set_id=group_permission_set_id, group_id=group_id, permission=permission)
        permissionItem.permission = permission
        permissionItem.save()
        return permissionItem

    @classmethod
    def grant_branch_global_permission(self, repo_id, refname, permission):
        if permission not in PERMISSION.VIEW:
            return None
        branchPermission = self.get_branchPermission_by_repoId_refname(repo_id, refname)
        if not branchPermission:
            branchPermission = RepoPermission(repo_id=repo_id, refname=refname)
        branchPermission.global_permission = permission
        branchPermission.save()
        return branchPermission

    @classmethod
    def grant_branch_user_permission(self, repo_id, refname, user_id, permission):
        if permission not in PERMISSION.VIEW:
            return None
        branchPermission = self.get_branchPermission_by_repoId_refname(repo_id, refname)
        if not branchPermission:
            branchPermission = BranchPermission(repo_id=repo_id, refname=refname)
            branchPermission.save()
        user_permission_set_id = branchPermission.user_permission_set_id
        permissionItem = self.get_permissionItem_by_setId_userId(user_permission_set_id, user_id)
        if not permissionItem:
            if user_permission_set_id == 0:
                permissionItem = PermissionItem(repo_id=repo_id, user_id=user_id, permission=permission)
                permissionItem.save()
                permissionItem.set_id = permissionItem.id
                branchPermission.user_permission_set_id = permissionItem.set_id
                branchPermission.save()
            else:
                permissionItem = PermissionItem(repo_id=repo_id, set_id=user_permission_set_id, user_id=user_id, permission=permission)
        permissionItem.permission = permission
        permissionItem.save()
        return permissionItem

    @classmethod
    def grant_branch_group_permission(self, repo_id, refname, group_id, permission):
        if permission not in PERMISSION.VIEW:
            return None
        branchPermission = self.get_branchPermission_by_repoId_refname(repo_id, refname)
        if not branchPermission:
            branchPermission = BranchPermission(repo_id=repo_id, refname=refname)
            branchPermission.save()
        group_permission_set_id = branchPermission.group_permission_set_id
        permissionItem = self.get_permissionItem_by_setId_groupId(group_permission_set_id, group_id)
        if not permissionItem:
            if group_permission_set_id == 0:
                permissionItem = PermissionItem(repo_id=repo_id, group_id=group_id, permission=permission)
                permissionItem.save()
                permissionItem.set_id = permissionItem.id
                branchPermission.group_permission_set_id = permissionItem.set_id
                branchPermission.save()
            else:
                permissionItem = PermissionItem(repo_id=repo_id, set_id=group_permission_set_id, group_id=group_id, permission=permission)
        permissionItem.permission = permission
        permissionItem.save()
        return permissionItem

    @classmethod
    def remove_permission_item(self, repo_id, id):
        permissionItem = get(PermissionItem, id)
        if permissionItem and permissionItem.repo_id == repo_id:
            permissionItem.visibly = 1
            permissionItem.save()
        return permissionItem

    # other
    @classmethod
    def get_current_user(self, user, userprofile):
        current_user_id = userprofile.current_user_id
        if current_user_id == 0 or current_user_id == userprofile.id:
            return user
        teamMember = TeamManager.get_teamMember_by_teamUserId_userId(current_user_id, userprofile.id)
        if not teamMember:
            return user
        current_user = GsuserManager.get_user_by_id(current_user_id)
        if not current_user:
            return user
        return current_user

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

