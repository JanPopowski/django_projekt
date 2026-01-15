
#!/usr/bin/bash
docker compose run -w /usr/src/app/ --rm backend python3 manage.py "$@"