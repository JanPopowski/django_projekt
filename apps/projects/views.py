from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .forms import AddMemberForm, ProjectForm, TaskForm
from .models import Comment, Project, Task, Team
from .permissions import IsTeamMember, IsTeamOwner
from .serializers import AddMemberSerializer, CommentSerializer, ProjectSerializer, TaskSerializer, TeamSerializer


class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def get_queryset(self):
        return (
            Team.objects.prefetch_related("members")
            .select_related("owner")
            .filter(members=self.request.user)
            .distinct()
        )

    def perform_create(self, serializer):
        team = serializer.save(owner=self.request.user)
        team.members.add(self.request.user)

    # Dodatkowa akcja: POST /api/teams/{id}/add_member/
    @action(detail=True, methods=["post"], permission_classes=[IsTeamOwner])
    def add_member(self, request, pk=None):
        team = self.get_object()
        serializer = AddMemberSerializer(data=request.data)

        if serializer.is_valid():
            user_to_add = serializer.validated_data["login_or_email"]

            if user_to_add in team.members.all():
                return Response({"message": "Użytkownik już jest w zespole"}, status=status.HTTP_400_BAD_REQUEST)

            team.members.add(user_to_add)
            return Response(
                {"message": f"Dodano użytkownika {user_to_add.username} do zespołu"}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """
        Endpoint: GET /api/projects/{id}/stats/
        Zwraca liczbę zadań ogółem vs. zakończonych.
        """
        project = self.get_object()

        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(status="done").count()

        return Response(
            {
                "project_id": project.id,
                "project_name": project.name,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "remaining_tasks": total_tasks - completed_tasks,
                "progress_percent": round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0,
            }
        )


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def get_queryset(self):
        return Project.objects.filter(team__members=self.request.user).distinct()


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def get_queryset(self):
        queryset = (
            Task.objects.select_related("project", "assigned_to")
            .filter(project__team__members=self.request.user)
            .distinct()
        )

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset


class MyTaskListView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.filter(assigned_to=user)

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)
        else:
            queryset = queryset.exclude(status="done")

        from django.db.models import F

        return queryset.order_by(F("due_date").asc(nulls_last=True), "created_at")


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def get_queryset(self):
        queryset = Comment.objects.filter(task__project__team__members=self.request.user)

        task_id = self.request.query_params.get("task")
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        
        
        
# --- WIDOKI HTML (FRONTEND) ---

class DashboardView(LoginRequiredMixin, ListView):
    template_name = 'dashboard.html'
    context_object_name = 'my_tasks'

    def get_queryset(self):
        # Dashboard: Moje pilne zadania (wszystko co nie jest done)
        return Task.objects.filter(assigned_to=self.request.user).exclude(status='done').order_by('due_date')

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(team__members=self.request.user).distinct()

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        # Zabezpieczenie: user widzi tylko swoje projekty
        return Project.objects.filter(team__members=self.request.user).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = self.object.tasks.select_related('assigned_to').all()
        # Rozdzielamy zadania na kolumny KANBAN
        context['todo_tasks'] = tasks.filter(status='todo')
        context['in_progress_tasks'] = tasks.filter(status='in_progress')
        context['done_tasks'] = tasks.filter(status='done')
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('project-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Przekazujemy usera do formularza
        return kwargs

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        kwargs['project'] = project
        return kwargs

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        form.instance.project = project
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project-detail', kwargs={'pk': self.kwargs['project_id']})
    
    
class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('project-list')
    
    def get_queryset(self):
        return Project.objects.filter(team__members=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    
class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/confirm_delete.html'
    success_url = reverse_lazy('project-list')
    
    def get_queryset(self):
        # Tylko właściciel zespołu może usuwać projekty (opcjonalna logika)
        return Project.objects.filter(team__owner=self.request.user)

# 2. Edycja i Usuwanie Zadania
class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'
    
    def get_queryset(self):
        return Task.objects.filter(project__team__members=self.request.user)

    def get_success_url(self):
        return reverse('project-detail', kwargs={'pk': self.object.project.id})
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.object.project
        return kwargs

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'projects/confirm_delete.html'
    
    def get_queryset(self):
        return Task.objects.filter(project__team__members=self.request.user)

    def get_success_url(self):
        return reverse('project-detail', kwargs={'pk': self.object.project.id})

# 3. Zarządzanie Zespołami (Lista i Dodawanie członków)
class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = 'projects/team_list.html'
    context_object_name = 'teams'

    def get_queryset(self):
        return Team.objects.filter(members=self.request.user)

class TeamDetailView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = 'projects/team_detail.html'
    
    def get_queryset(self):
        return Team.objects.filter(members=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['add_member_form'] = AddMemberForm()
        return context

class TeamAddMemberView(LoginRequiredMixin, FormView):
    form_class = AddMemberForm
    template_name = 'projects/team_detail.html' # W razie błędu

    def form_valid(self, form):
        team = get_object_or_404(Team, pk=self.kwargs['pk'], owner=self.request.user)
        username = form.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
            team.members.add(user)
            messages.success(self.request, f"Dodano użytkownika {username}.")
        except User.DoesNotExist:
            messages.error(self.request, "Użytkownik nie istnieje.")
        
        return redirect('team-detail', pk=team.pk)
    
class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    fields = ['name']
    template_name = 'projects/team_form.html'
    success_url = reverse_lazy('team-list')

    def form_valid(self, form):
        team = form.save(commit=False)
        team.owner = self.request.user
        team.save()
        team.members.add(self.request.user)
        return super().form_valid(form)
    
    
@login_required
def update_task_status(request, pk, status):
    task = get_object_or_404(Task, pk=pk, project__team__members=request.user)
    
    if status in dict(Task.STATUS_CHOICES):
        task.status = status
        task.save()
    
    return redirect('project-detail', pk=task.project.id)
