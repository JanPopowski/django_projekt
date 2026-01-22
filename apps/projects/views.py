from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .forms import AddMemberForm, CommentForm, ProjectForm, TaskForm
from .models import Project, Task, Team
from .permissions import IsTeamMember
from .serializers import ProjectSerializer, TaskSerializer


class ProjectViewSet(viewsets.GenericViewSet):
    """
    ViewSet ograniczony tylko do obsługi statystyk.
    Dziedziczy po GenericViewSet, aby nie wystawiać automatycznie 
    endpointów CRUD (list, create, delete).
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]

    def get_queryset(self):
        return Project.objects.filter(team__members=self.request.user).distinct()
    
    @extend_schema(
        summary="Pobierz statystyki projektu",
        description="Zwraca liczbę zadań ogółem i zakończonych dla danego projektu.",
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """
        Endpoint: GET /api/projects/{id}/stats/
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


class MyTaskListView(generics.ListAPIView):
    """
    Endpoint: GET /api/my-tasks/
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        queryset = Task.objects.select_related("project", "project__team").filter(assigned_to=user)

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)
        else:
            # Domyślnie wykluczamy zakończone, jeśli nie podano statusu
            queryset = queryset.exclude(status="done")

        return queryset.order_by(F("due_date").asc(nulls_last=True), "created_at")

    @extend_schema(
        summary="Pobierz moje zadania",
        parameters=[
            OpenApiParameter(
                name='status',
                description='Filtruj po statusie (todo, in_progress, done)',
                required=False,
                type=OpenApiTypes.STR,
                enum=['todo', 'in_progress', 'done']
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
        
        
        
# --- WIDOKI HTML (FRONTEND) ---

class DashboardView(LoginRequiredMixin, ListView):
    template_name = 'dashboard.html'
    context_object_name = 'my_tasks'

    def get_queryset(self):
        return Task.objects.filter(assigned_to=self.request.user).exclude(status='done').order_by('due_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teams'] = Team.objects.filter(members=self.request.user).distinct()
        return context

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
        kwargs['user'] = self.request.user
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
        
        context['add_member_form'] = AddMemberForm(team=self.object)
        
        return context
class TeamAddMemberView(LoginRequiredMixin, FormView):
    form_class = AddMemberForm
    template_name = 'projects/team_detail.html'

    def get_form_kwargs(self):
        """
        Przekazujemy instancję zespołu do formularza,
        aby metoda clean() mogła wykonać walidację.
        """
        kwargs = super().get_form_kwargs()
        team = get_object_or_404(Team, pk=self.kwargs['pk'], owner=self.request.user)
        kwargs['team'] = team
        return kwargs

    def form_valid(self, form):
        team = form.team
        user = form.user_to_add
        
        team.members.add(user)
        messages.success(self.request, f"Dodano użytkownika {user.username} do zespołu.")
        
        return redirect('team-detail', pk=team.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = get_object_or_404(Team, pk=self.kwargs['pk'], owner=self.request.user)
        return context
    
    
    
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


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'projects/task_detail.html'
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['comments'] = self.object.comments.all().order_by('created_at')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = self.object
            comment.author = request.user
            comment.save()
            return redirect('task-detail', pk=self.object.pk)
        
        context = self.get_context_data()
        context['comment_form'] = form
        return self.render_to_response(context)
