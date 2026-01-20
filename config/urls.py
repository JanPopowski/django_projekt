"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.projects.views import CommentViewSet, MyTaskListView, ProjectViewSet, TaskViewSet, TeamViewSet
from apps.users.views import MyProfileView

router = DefaultRouter()
router.register(r"teams", TeamViewSet, basename="team")
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"comments", CommentViewSet, basename="comment")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.jwt")),
    path("my-profile/", MyProfileView.as_view(), name="my_profile"),
    path("my-tasks", MyTaskListView.as_view(), name="my_tasks"),
    path("", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
