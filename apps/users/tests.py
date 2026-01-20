from django.test import TestCase
from django.contrib.auth.models import User
from .models import Profile

class UserSignalTests(TestCase):
    def test_profile_created_on_user_creation(self):
        """
        Sprawdza, czy po stworzeniu Usera automatycznie tworzy się Profile.
        """
        user = User.objects.create_user(username='newuser', password='password123')
        
        # Sprawdzamy czy profil istnieje
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(user.profile.user.username, 'newuser')