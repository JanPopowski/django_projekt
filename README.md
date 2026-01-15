Wymagania Funkcjonalne

Użytkownicy i Profile 6 pkt

Dostęp: System dostępny tylko dla zalogowanych użytkowników.

Rejestracja i Logowanie: Standardowy mechanizm uwierzytelniania.

Profil: Możliwość edycji danych ("O mnie") oraz wgrania Avatara (ImageField), widocznego przy zadaniach i komentarzach.

Reset hasła: Mechanizm odzyskiwania hasła (linki resetujące logowane w konsoli).
Struktura Organizacyjna 8 pkt

Zespoły: Użytkownik może utworzyć Zespół i automatycznie staje się jego właścicielem.

Członkostwo: Właściciel może dodać do zespołu innego, zarejestrowanego użytkownika (wpisując jego login/email w formularzu).

Projekty: W ramach Zespołu można tworzyć wiele Projektów.

Izolacja danych: Użytkownik widzi Projekty i Zadania tylko tych Zespołów, do których należy. Próba dostępu do danych obcego zespołu musi skutkować błędem (403/404).
Tablica Zadań (Główny widok Projektu) 8 pkt

Struktura Zadania: Tytuł, Opis, Priorytet (High/Medium/Low), Data wykonania (Due Date), Status (np. To Do, In Progress, Done).

Przypisanie: Możliwość przypisania zadania do członka zespołu (lista rozwijana w formularzu ograniczona tylko do członków danego zespołu).

Widok Kanban: Zadania w projekcie wyświetlane są w kolumnach odpowiadających ich statusom.

Zmiana Statusu: Łatwy sposób na zmianę statusu (np. przycisk na karcie zadania "Przesuń dalej" lub edycja).
Szczegóły Zadania 6 pkt

Komentarze: Dyskusja pod zadaniem (widoczny autor i data).

Załączniki: Możliwość dodania pliku do zadania (np. dokumentacja, screenshot).
Dashboard Osobisty 6 pkt
Strona startowa po zalogowaniu zawiera:

Listę Zespołów użytkownika.

Sekcję "Moje pilne zadania": Lista zadań przypisanych do mnie, które nie są jeszcze zakończone.
API (Dla zewnętrznych integracji) 6 pkt
System wystawia endpointy JSON (wymagane uwierzytelnienie jwt):

GET /api/projects/{id}/stats/ - Zwraca statystyki projektu (liczba zadań ogółem vs. zakończonych).

GET /api/my-tasks/?status=todo - Zwraca listę moich zadań z możliwością filtrowania po statusie.
Wymagania Techniczne

Technologia i Konfiguracja:

Backend: Django + Django Rest Framework.

Repozytorium z plikiem .gitignore i requirements.txt.

Poprawna konfiguracja MEDIA_ROOT do obsługi wgrywanych plików.

Skonfigurowany Ruff (linter).
Modele i Baza Danych:

Zastosowanie relacji OneToMany (Projekt-Zadania) oraz ManyToMany (Użytkownik-Zespół).

Optymalizacja: Użycie select_related / prefetch_related w widokach (np. pobieranie zadań wraz z autorami), aby uniknąć problemu N+1 zapytań.
Widoki i Szablony:

Użycie Class Based Views (ListView, DetailView, CreateView, UpdateView).

Wspólny szablon bazowy (base.html).
Formularze i Walidacja:

Wykorzystanie ModelForm.

Zaimplementowanie customowej walidacji w metodzie clean() (np. "Nie można dodać użytkownika, który już jest w zespole").
API (DRF):

Wykorzystanie ViewSet i Router.

Automatyczna dokumentacja Swagger (drf-spectacular).
Testy:

Napisanie testów automatycznych skupiających się na kluczowych funkcjonalnościach (np. customowe walidacje czy próba dostępu użytkownika z Zespołu A do zasobów Zespołu B)