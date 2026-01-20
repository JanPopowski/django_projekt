from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .forms import CustomUserCreationForm, ProfileForm
from .models import Profile
from .serializers import ProfileSerializer


class MyProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile
    
    
class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        # Automatyczne logowanie po rejestracji
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'users/profile_form.html'
    success_url = reverse_lazy('my_profile')

    def get_object(self):
        return self.request.user.profile
    
class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'users/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self):
        # Wyświetlamy profil zalogowanego użytkownika
        return self.request.user.profile

