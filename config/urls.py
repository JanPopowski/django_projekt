from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

# Import widoków logowania/wylogowania
from django.contrib.auth import views as auth_views
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

# Import widoków API oraz Frontendowych (DashboardView, ProjectListView itd.)
from apps.projects.views import (
    CommentViewSet,
    DashboardView,
    MyTaskListView,
    ProjectCreateView,
    ProjectDeleteView,
    ProjectDetailView,
    ProjectListView,
    ProjectUpdateView,
    ProjectViewSet,
    TaskCreateView,
    TaskDeleteView,
    TaskUpdateView,
    TaskViewSet,
    TeamAddMemberView,
    TeamCreateView,
    TeamDetailView,
    TeamListView,
    TeamViewSet,
)
from apps.users.views import MyProfileView, ProfileDetailView, ProfileUpdateView, RegisterView

router = DefaultRouter()
router.register(r"teams", TeamViewSet, basename="api-team")
router.register(r"projects", ProjectViewSet, basename="api-project")
router.register(r"tasks", TaskViewSet, basename="api-task")
router.register(r"comments", CommentViewSet, basename="api-comment")

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- FRONTEND: AUTH (Logowanie) ---
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/profile/', ProfileDetailView.as_view(), name='my_profile'),
    path('accounts/profile/edit', ProfileUpdateView.as_view(), name='profile_edit'),
    path('accounts/register/', RegisterView.as_view(), name='register'),
    # --- FRONTEND: DASHBOARD (Strona startowa) ---
    # Jeśli user niezalogowany -> przekieruje na login (dzięki LoginRequiredMixin w widoku)
    # Jeśli zalogowany -> pokaże Dashboard
    path('', DashboardView.as_view(), name='dashboard'),

    # --- FRONTEND: PROJEKTY I ZADANIA ---
    path('projects/', ProjectListView.as_view(), name='project-list'),
    path('projects/add/', ProjectCreateView.as_view(), name='project-create'),
    path('projects/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('projects/<int:project_id>/add-task/', TaskCreateView.as_view(), name='task-create'),
        
    path('projects/<int:pk>/edit/', ProjectUpdateView.as_view(), name='project-edit'),
    path('projects/<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),

    path('tasks/<int:pk>/edit/', TaskUpdateView.as_view(), name='task-edit'),
    path('tasks/<int:pk>/delete/', TaskDeleteView.as_view(), name='task-delete'),

    path('teams/', TeamListView.as_view(), name='team-list'),
    path('teams/add/', TeamCreateView.as_view(), name='team-create'),
    path('teams/<int:pk>/', TeamDetailView.as_view(), name='team-detail'),
    path('teams/<int:pk>/add-member/', TeamAddMemberView.as_view(), name='team-add-member'),


    # --- API (Backend) ---
    # Wszystkie ścieżki API przesuwamy pod /api/, żeby zwolnić główny adres dla Dashboardu
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.jwt")),
    
    path("api/my-profile/", MyProfileView.as_view(), name="api_my_profile"),
    path("api/my-tasks/", MyTaskListView.as_view(), name="api_my_tasks"),
    
    # Router API na końcu
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)