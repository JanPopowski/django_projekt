from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import Team, Project, Task

class ProjectTests(APITestCase):
    def setUp(self):
        # 1. Tworzymy użytkowników
        self.user_a = User.objects.create_user(username='user_a', password='password123')
        self.user_b = User.objects.create_user(username='user_b', password='password123') # Kolega z zespołu A
        self.user_intruder = User.objects.create_user(username='intruder', password='password123') # Obcy (Zespół B)

        # 2. Tworzymy Zespół A
        self.team_a = Team.objects.create(name='Team A', owner=self.user_a)
        self.team_a.members.add(self.user_a)
        self.team_a.members.add(self.user_b)

        # 3. Tworzymy Zespół B (Dla intruza)
        self.team_b = Team.objects.create(name='Team B', owner=self.user_intruder)
        self.team_b.members.add(self.user_intruder)

        # 4. Tworzymy Projekt w Zespole A
        self.project_a = Project.objects.create(name='Project A', description='Desc', team=self.team_a)

        # URL-e
        self.projects_url = reverse('project-list') # /api/projects/
        self.tasks_url = reverse('task-list')       # /api/tasks/

    def test_isolation_data_access(self):
        """
        Testuje Izolację Danych: Użytkownik z Zespołu B nie może widzieć projektu Zespołu A.
        """
        # Logujemy się jako Intruz
        self.client.force_authenticate(user=self.user_intruder)

        # Próba pobrania listy projektów
        response = self.client.get(self.projects_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Sprawdzamy, czy lista jest pusta (nie widzi Project A)
        self.assertEqual(len(response.data), 0)

        # Próba bezpośredniego dostępu do ID projektu
        detail_url = reverse('project-detail', args=[self.project_a.id])
        response = self.client.get(detail_url)
        
        # Powinien dostać 404 (Not Found) - system udaje, że projekt nie istnieje
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_can_see_project(self):
        """
        Testuje, czy członek zespołu widzi projekt.
        """
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get(self.projects_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Project A')

    def test_custom_validation_task_assignment(self):
        """
        Testuje Customową Walidację: Nie można przypisać zadania użytkownikowi spoza zespołu.
        """
        self.client.force_authenticate(user=self.user_a) # Właściciel

        data = {
            'title': 'Tajne Zadanie',
            'description': 'Opis',
            'project': self.project_a.id,
            'assigned_to': self.user_intruder.id, # <--- PRÓBA PRZYPISANIA OBCEGO
            'priority': 'high'
        }

        response = self.client.post(self.tasks_url, data)
        
        # Oczekujemy błędu 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Sprawdzamy treść błędu (czy walidator zadziałał)
        self.assertIn('assigned_to', response.data)

    def test_only_owner_can_add_members(self):
        """
        Testuje Uprawnienia: Zwykły członek nie może dodawać ludzi do zespołu.
        """
        self.client.force_authenticate(user=self.user_b) # Zwykły członek

        url = reverse('team-add-member', args=[self.team_a.id])
        data = {'login_or_email': 'intruder'}

        response = self.client.post(url, data)
        
        # Oczekujemy błędu 403 Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_task_happy_path(self):
        """
        Testuje poprawne stworzenie zadania.
        """
        self.client.force_authenticate(user=self.user_a)
        data = {
            'title': 'Legalne Zadanie',
            'description': 'Opis',
            'project': self.project_a.id,
            'assigned_to': self.user_b.id, # <--- Przypisanie kolegi z zespołu (OK)
            'priority': 'medium'
        }
        response = self.client.post(self.tasks_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)