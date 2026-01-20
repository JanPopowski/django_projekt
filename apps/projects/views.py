from django.shortcuts import render
from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Team, Project, Task, Comment
from .serializers import TeamSerializer, ProjectSerializer, AddMemberSerializer, TaskSerializer, CommentSerializer
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


    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Endpoint: GET /api/projects/{id}/stats/
        Zwraca liczbę zadań ogółem vs. zakończonych.
        """
        project = self.get_object()
        
        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(status='done').count()
        
        return Response({
            "project_id": project.id,
            "project_name": project.name,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "remaining_tasks": total_tasks - completed_tasks,
            "progress_percent": round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0
        })

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def get_queryset(self):
        return Project.objects.filter(team__members=self.request.user).distinct()
    
    


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]
    
    def get_queryset(self):
        queryset = Task.objects.filter(project__team__members=self.request.user).distinct()
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        return queryset
    
class MyTaskListView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.filter(assigned_to=user)

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        else:
            queryset = queryset.exclude(status='done')

        from django.db.models import F
        return queryset.order_by(F('due_date').asc(nulls_last=True), 'created_at')
    
    
    
class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def get_queryset(self):
        queryset = Comment.objects.filter(task__project__team__members=self.request.user)
        
        task_id = self.request.query_params.get('task')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        
        
