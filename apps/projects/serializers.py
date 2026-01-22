from rest_framework import serializers

from .models import Project, Task


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name"]


class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    team_name = serializers.CharField(source="project.team.name", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", 
            "title", 
            "description", 
            "priority", 
            "status", 
            "due_date",
            "attachment",
            "project",
            "project_name",
            "team_name",
            "created_at"
        ]
        read_only_fields = ["created_at"]