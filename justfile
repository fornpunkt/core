# load .env file
set dotenv-load

@_default:
  just --list

# setup virtual environment, install dependencies, and run migrations
setup:
  python3 -m venv .venv
  ./.venv/bin/pip install -r requirements.txt
  ./.venv/bin/python -Wa manage.py migrate

run:
  ./.venv/bin/python -Wa manage.py runserver

test:
  ./.venv/bin/python -Wa manage.py test

# virtual environment wrapper for manage.py
manage *COMMAND:
  ./.venv/bin/python manage.py 

