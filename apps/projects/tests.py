from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Project, Task, Team


class ProjectTests(TestCase):
    def setUp(self):
        # 1. Tworzenie użytkowników
        self.user_a = User.objects.create_user(username='user_a', password='password123')
        self.user_b = User.objects.create_user(username='user_b', password='password123')
        self.user_intruder = User.objects.create_user(username='intruder', password='password123')

        # 2. Tworzenie Zespołów (Team)
        self.team_a = Team.objects.create(name='Team A', owner=self.user_a)
        self.team_a.members.add(self.user_a)
        self.team_a.members.add(self.user_b)

        self.team_b = Team.objects.create(name='Team B', owner=self.user_intruder)
        self.team_b.members.add(self.user_intruder)

        # 3. Tworzenie Projektu
        self.project_a = Project.objects.create(name='Project A', description='Desc', team=self.team_a)

    def test_isolation_data_access(self):
        """
        Testuje Izolację Danych: Intruz nie widzi projektu Zespołu A.
        """
        # Używamy login() zamiast force_authenticate
        self.client.login(username='intruder', password='password123')

        # Zamiast 'project-list' sprawdzamy Dashboard
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Sprawdzamy HTML - tekst "Project A" NIE powinien się pojawić
        self.assertNotContains(response, 'Project A')

        # Bezpośredni dostęp do szczegółów
        detail_url = reverse('project-detail', args=[self.project_a.id])
        response = self.client.get(detail_url)
        
        # Oczekujemy braku dostępu (403 lub 404)
        self.assertIn(response.status_code, [403, 404])

    def test_member_can_see_project(self):
        """
        Testuje, czy członek zespołu widzi projekt (ma dostęp do jego szczegółów).
        """
        self.client.login(username='user_b', password='password123')
        
        # ZMIANA: Zamiast Dashboardu, sprawdzamy bezpośrednio stronę projektu
        detail_url = reverse('project-detail', args=[self.project_a.id])
        response = self.client.get(detail_url)
        
        # Jeśli User B jest w zespole, powinien wejść (200 OK) i widzieć nazwę
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Project A')

    def test_create_task_happy_path(self):
        """
        Testuje poprawne stworzenie zadania przez formularz HTML.
        """
        self.client.login(username='user_a', password='password123')
        
        # URL formularza tworzenia zadania (zwróć uwagę na kwargs)
        url = reverse('task-create', kwargs={'project_id': self.project_a.id})
        
        data = {
            'title': 'Legalne Zadanie',
            'description': 'Opis',
            'priority': 'medium',
            'status': 'todo',
            'assigned_to': self.user_b.id
        }
        
        # Wysyłamy POST
        response = self.client.post(url, data)
        
        # W Django sukces formularza to zazwyczaj przekierowanie (302), a nie 201 Created
        self.assertEqual(response.status_code, 302)
        
        # Sprawdzamy w bazie czy obiekt powstał
        self.assertTrue(Task.objects.filter(title='Legalne Zadanie').exists())

    # --- UWAGA: Poniższe testy mogą wymagać dopasowania logiki w views.py ---
    
    def test_custom_validation_task_assignment(self):
        """
        Testuje, czy formularz blokuje przypisanie zadania osobie spoza zespołu.
        """
        self.client.login(username='user_a', password='password123')
        url = reverse('task-create', kwargs={'project_id': self.project_a.id})

        data = {
            'title': 'Tajne Zadanie',
            'description': 'Opis',
            'priority': 'high',
            'status': 'todo',
            # Próbujemy przypisać intruza
            'assigned_to': self.user_intruder.id 
        }

        response = self.client.post(url, data)
        
        # Jeśli walidacja działa, formularz powinien zwrócić 200 (strona z błędami), a nie przekierowanie (302)
        self.assertEqual(response.status_code, 200)
        
        # Sprawdzamy czy w HTML pojawił się błąd formularza
        # (To zadziała tylko jeśli masz walidację w metodzie clean() formularza)
        self.assertFalse(Task.objects.filter(title='Tajne Zadanie').exists())