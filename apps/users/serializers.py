from rest_framework import serializers
from djoser.serializers import UserCreateSerializer 
from .models import Profile

class CustomUserCreateSerializer(UserCreateSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        fields = ('username', 'password', 'email', 'first_name', 'last_name')



class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)


    class Meta:
        model = Profile
        fields = ('username', 'bio', 'avatar', 'first_name', 'last_name')