# FornPunkt
 
This code repository holds the core monolith serving FornPunk.se.
 
### Development environment setup
 
The development environment is managed with [devenv](https://devenv.sh/). Once devenv is installed, run:
 
```
devenv shell
setup
run
```
 
Entering the shell installs Python 3.11.7 and the dependencies from `requirements.txt` into a virtual environment. `setup` runs database migrations and `run` starts the development server.
 
### Testing
 
```
python manage.py test
```
alternatively using coverage (only for identifying missing smoke tests)
 
```
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```
 
### Environment variables
 
All variables have default values suitable for development.
 
#### Production variables
 
 - `FP_ENVIRONMENT` - must be set to `production`
 - `DJANGO_ALLOWED_HOSTS`
 - `FP_SECRET_KEY`
 - `DISABLE_COLLECTSTATIC` - must be set to `1`
 - `DATABASE_URL`
 - `FP_EMAIL_USER` - SMTP username
 - `FP_EMAIL_PASSWORD` - SMTP password
 - `SENTRY_DSN_URI`
 - `SENTRY_SEND_DEFAULT_PII` - should only be set for debugging purposes
 - `ADMIN_PATH`
 - `HASHIDS_SALT`
 - `FP_EMAIL_HOST` FornPunkt

