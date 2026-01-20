from django.db import models
from django.contrib.auth.models import User

class Team(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nazwa zespołu")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_teams')
    members = models.ManyToManyField(User, related_name='teams', blank=True)
    def __str__(self):
        return self.name

class Project(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nazwa projektu")
    description = models.TextField(verbose_name="Opis projektu")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='projects')

    def __str__(self):
        return self.name
