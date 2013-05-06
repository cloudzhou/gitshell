from django.db import models

class BaseModel(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)

    class Meta:
        abstract = True
    
class Count(models.Model):
    count = models.IntegerField(default=0, null=False)     

class Select(models.Model):
    pass

class CacheKey:
    REFS_BRANCH = 'repo.refs_branch_%s'
    REFS_TAG = 'repo.refs_tag_%s'
    REFS_REPO_COMMIT_VERSION = 'repo.commit_version_%s'
    REFS_COMMIT_HASH = 'repo.refs_commit_hash_%s_%s_%s'
