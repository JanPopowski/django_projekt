from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Team, Project
from .serializers import TeamSerializer, ProjectSerializer, AddMemberSerializer
from .permissions import IsTeamMember, IsTeamOwner

class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def get_queryset(self):
        return Team.objects.filter(members=self.request.user).distinct()

    def perform_create(self, serializer):
        team = serializer.save(owner=self.request.user)
        team.members.add(self.request.user)

    # Dodatkowa akcja: POST /api/teams/{id}/add_member/
    @action(detail=True, methods=['post'], permission_classes=[IsTeamOwner])
    def add_member(self, request, pk=None):
        team = self.get_object()
        serializer = AddMemberSerializer(data=request.data)
        
        if serializer.is_valid():
            user_to_add = serializer.validated_data['login_or_email']
            
            if user_to_add in team.members.all():
                return Response({"message": "Użytkownik już jest w zespole"}, status=status.HTTP_400_BAD_REQUEST)
            
            team.members.add(user_to_add)
            return Response({"message": f"Dodano użytkownika {user_to_add.username} do zespołu"}, 
                            status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def get_queryset(self):
        return Project.objects.filter(team__members=self.request.user).distinct()