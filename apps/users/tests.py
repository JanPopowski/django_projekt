from django.contrib.auth.models import User
from django.test import TestCase


class UserSignalTests(TestCase):
    def test_profile_created_on_user_creation(self):
        """
        Sprawdza, czy po stworzeniu Usera automatycznie tworzy się Profile.
        """
        user = User.objects.create_user(username='newuser', password='password123')
        user.refresh_from_db()
        
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.user.username, 'newuser')