from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import serializers

from .models import Comment, Project, Task, Team


class TeamSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Team
        fields = ["id", "name", "description", "owner", "members"]
        read_only_fields = ["members", "created_at"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "description", "team"]

    def validate_team(self, value):
        request = self.context.get('request')
        # FIX: Swagger nie ma usera, więc pomijamy walidację przy generowaniu schematu
        if request and request.user and request.user.is_authenticated:
            if not request.user.teams.filter(pk=value.pk).exists():
                raise serializers.ValidationError("Nie należysz do tego zespołu.")
        return value


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "project", "assigned_to", 
            "priority", "status", "due_date", "attachment", "created_at"
        ]
        read_only_fields = ["created_at"]

    def validate_project(self, value):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            if not value.team.members.filter(pk=request.user.pk).exists():
                raise serializers.ValidationError("Nie masz dostępu do tego projektu.")
        return value

    def validate(self, data):
        # Walidacja logiczna: czy przypisana osoba jest w zespole projektu?
        project = data.get('project') or (self.instance.project if self.instance else None)
        assigned_to = data.get('assigned_to')

        if project and assigned_to:
            if not project.team.members.filter(pk=assigned_to.pk).exists():
                raise serializers.ValidationError({"assigned_to": "Użytkownik nie jest członkiem zespołu tego projektu."})
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "task", "author", "content", "created_at"]

    def validate_task(self, value):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            if not value.project.team.members.filter(pk=request.user.pk).exists():
                raise serializers.ValidationError("Nie masz dostępu do tego zadania.")
        return value


class AddMemberSerializer(serializers.Serializer):
    login_or_email = serializers.CharField(write_only=True)

    def validate_login_or_email(self, value):
        user = User.objects.filter(Q(username=value) | Q(email=value)).first()
        if not user:
            raise serializers.ValidationError("Użytkownik o podanym loginie lub emailu nie istnieje.")
        return user