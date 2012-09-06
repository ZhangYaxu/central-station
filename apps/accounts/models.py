__author__ = 'Derek Stegelman'
__date__ = '9/5/12'


from django.db import models
from django.contrib.auth.models import User

from hadrian.utils.slugs import unique_slugify

from base import AuditBase

class Account(models.Model):
    company_name = models.CharField(max_length=250, blank=True, null=True)
    slug = models.SlugField()

    # Main.
    is_active = models.BooleanField()
    is_deleted = models.BooleanField()

    def __unicode__(self):
        return self.sub_domain

    def save(self, *args, **kwargs):
        unique_slugify(self, self.company_name)
        super(Account, self).save(*args, **kwargs)

class Team(AuditBase):
    name = models.CharField(max_length=250, blank=True, null=True)
    organization = models.ForeignKey(Account)

class UserProfile(AuditBase):
    user = models.ForeignKey(User)
    teams = models.ManyToManyField(Team)

    def __unicode__(self):
        return self.user.username

    @property
    def role(self, team):
        assigned_role = RoleAssigned.objects.get(user=self.user, team=team)
        return assigned_role.role.name

class Role(AuditBase):
    name = models.CharField(max_length=250)

class RoleAssigned(AuditBase):
    user = models.ForeignKey(User)
    team = models.ForeignKey(Team)
    role = models.ForeignKey(Role)