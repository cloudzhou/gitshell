from django.db import models

class Count(models.Model):
    count = models.IntegerField(default=0, null=False)     

class Select(models.Model):
    pass
