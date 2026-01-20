from rest_framework import serializers
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Team, Project

class TeamSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'owner', 'members', 'created_at']
        read_only_fields = ['members', 'created_at']

class AddMemberSerializer(serializers.Serializer):
    login_or_email = serializers.CharField(write_only=True)

    def validate_login_or_email(self, value):
        user = User.objects.filter(Q(username=value) | Q(email=value)).first()
        if not user:
            raise serializers.ValidationError("Użytkownik o podanym loginie lub emailu nie istnieje.")
        return user

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'team', 'created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            self.fields['team'].queryset = Team.objects.filter(members=request.user)
            
            
from .models import Team, Project, Task, Comment


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'project', 'assigned_to', 
            'priority', 'status', 'due_date', 'attachment', 'created_at'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        
        if request and hasattr(request, 'user'):
            self.fields['project'].queryset = Project.objects.filter(team__members=request.user)
            self.fields['assigned_to'].queryset = User.objects.filter(teams__members=request.user).distinct()

    def validate(self, data):
        user = data.get('assigned_to')
        project = data.get('project')

        # Jeśli aktualizujemy zadanie, 'project' może nie być przesłany, musimy go pobrać z instancji
        if not project and self.instance:
            project = self.instance.project

        if user and project:
            if user not in project.team.members.all():
                raise serializers.ValidationError({
                    "assigned_to": "Ten użytkownik nie jest przypisany do tego projektu."
                })
        return data
    
    
    
class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
        
    class Meta:
        model = Comment
        fields = ['id', 'task', 'author', 'content', 'created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            self.fields['task'].queryset = Task.objects.filter(
                project__team__members=request.user
            )