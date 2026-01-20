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