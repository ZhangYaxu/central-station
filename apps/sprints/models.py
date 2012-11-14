__author__ = 'Derek Stegelman'
__date__ = '9/5/12'

from django.db import models
from django.contrib.auth.models import User

from sprints.choices import STORY_STATUS_CHOICES, STORY_POINT_CHOICES, STATUS_COLORS, color_choices
from sprints.managers import SprintManager
from accounts.models import Team, Account
from projects.models import Project

from actstream import action

class AuditBase(models.Model):
    deleted = models.BooleanField()
    deleted_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    class Meta:
        abstract = True

class Sprint(AuditBase):
    name = models.CharField(max_length=250, blank=True, null=True)
    start_date = models.DateField(blank=False, null=True)
    end_date = models.DateField(blank=False, null=True)
    team = models.ForeignKey(Team) # TODO this should be M2M

    locked = models.BooleanField()

    objects = SprintManager()

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return "Sprint from %s through %s" % (str(self.start_date), str(self.end_date))

    def create(self, request):
        action.send(request.user, verb='created', action_object=self, target=self.team)

    def update(self, request):
        action.send(request.user, verb='updated', action_object=self, target=self.team)

    def total_points(self):
        points = 0
        for story in self.story_set.all():
            points = points + story.points
        return points

    def completed_points(self):
        points = 0
        for story in self.story_set.all():
            if story.story_status.slug == 'done':
                points = points + story.points
        return points

    def stories(self):
        return self.story_set.all()
            
    def perc(self):
        total = self.total_points()
        perc = []
        for status in self.team.organization.statuses():
            stories_of_a_certain_status = []
            #statuses.append(status.status)
            for story in self.stories():
                if story.story_status.slug == status.slug:
                    stories_of_a_certain_status.append(story)
            
            s = {
                'status' : status.status,
                'style_class': status.style_class
            }
            status_points = 0
            for story in stories_of_a_certain_status:
                status_points += story.points
            s['percentage'] = float(status_points) / float(total) * 100
            perc.append(s)

        return perc

    @models.permalink
    def get_absolute_url(self):
        return ('sprint_detail', (), { 'account': self.team.organization.slug, 'id': self.id })

    @models.permalink
    def get_story_add(self):
        return ('story_add', (), {'account': self.team.organization.slug})

    @models.permalink
    def get_task_add(self):
        return ('task_add', (), {'account': self.team.organization.slug})

    @models.permalink
    def get_sprint_edit(self):
        return ('sprint_edit', (), { 'account': self.team.organization.slug, 'id': self.id })

class StoryStatus(models.Model):
    account = models.ForeignKey(Account, null=True)
    status = models.CharField(max_length=250, blank=True, null=True)
    order = models.IntegerField(null=True, blank=True)
    slug = models.SlugField(null=True, blank=True)
    color = models.CharField(max_length=20, choices=color_choices())
    
    def __unicode__(self):
        return self.status

    @property
    def style_class(self):
        return STATUS_COLORS[self.color]['style_class']

    @property
    def hex_code(self):
        return STATUS_COLORS[self.color]['hex']

    class Meta:
        ordering = ['order']


class Story(AuditBase):
    title = models.CharField(max_length=250, blank=False, null=True)
    # Status no longer used.
    status = models.CharField(choices=STORY_STATUS_CHOICES, max_length=20, blank=True, null=True, editable=False)
    story_status = models.ForeignKey(StoryStatus, null=True, blank=True)
    position = models.IntegerField(blank=True, null=True)
    
    points = models.IntegerField(choices=STORY_POINT_CHOICES, blank=False, null=False, verbose_name="Difficulty")
    sprint = models.ForeignKey(Sprint, null=True, blank=True)
    project = models.ForeignKey(Project, null=True)

    def __unicode__(self):
        return self.title

    def create(self, request):
        action.send(request.user, verb='created', action_object=self, target=self.project)

    def close(self, request):
        self.status = 'done'
        action.send(request.user, verb='closed', action_object=self, target=self.project)
        self.save()

    def update(self, request):
        action.send(request.user, verb='updated', action_object=self, target=self.project)

    def mark_roadblocked(self, request):
        self.status = 'road-blocked'
        action.send(request.user, verb='marked as Road Blocked', action_object=self, target=self.project)

    @models.permalink
    def get_absolute_url(self):
        return ('story_edit', (), {'account': self.project.account.slug, 'pk': self.id})

    @property
    def roadblocked(self):
        for task in self.task_set.all():
            if task.status == 'road-blocked':
                return True
        return False

    class Meta:
        ordering = ['story_status']


class Task(AuditBase):
    title = models.CharField(max_length=250, blank=False, null=True)
    # Status not used anymore.
    status = models.CharField(choices=STORY_STATUS_CHOICES, max_length=20, blank=True, null=True)
    ticket = models.URLField(blank=True, null=True)
    assigned = models.ForeignKey(User, null=True)

    story = models.ForeignKey(Story, null=True)
    complete = models.BooleanField()

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('task_edit', (), {'account': self.story.sprint.team.organization.slug, 'pk': self.id})

    def create(self, request):
        action.send(request.user, verb='created', action_object=self, target=self.story)

    def update(self, request):
        action.send(request.user, verb='updated', action_object=self, target=self.story)

class Roadblock(AuditBase):
    title = models.CharField(max_length=250, blank=False, null=True)
    story = models.ForeignKey(Story, null=True, blank=False)

    def __unicode__(self):
        return self.title
        
        
class OrderedStory(AuditBase):
    story = models.ForeignKey(Story, null=True, blank=False)
    position = models.IntegerField(blank=False)
    status = models.CharField(choices=STORY_STATUS_CHOICES, max_length=20, blank=True, null=True)
