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
    
    
    
class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]

    title = models.CharField(max_length=200, verbose_name="Tytuł")
    description = models.TextField(verbose_name="Opis")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    due_date = models.DateField(null=True, blank=True, verbose_name="Termin wykonania")
    
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(verbose_name="Treść komentarza")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Komentarz {self.author} odnośnie {self.task}"