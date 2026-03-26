#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

Then create a file called `Procfile` (no extension, capital P) in the root:
```
web: gunicorn config.wsgi:application