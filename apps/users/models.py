from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="profile_images", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} profile"
