# Pub API

# Virtual Env

````bash
$ python3.7 -m venv env

$ source env/bin/activate
````

# python setup


````bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get -y -f install python3.7 python3-pip python3.7-dev python3.7-venv libpython3.7-dev python3-setuptools
sudo -H pip3 --default-timeout=50 install --upgrade pip
sudo -H pip3 install virtualenv
````

# usefull links

https://docs.djangoproject.com/en/4.1/intro/tutorial01/

# Install reqs

````
pip install -r requirements.txt 

pip freeze > requirements.txt

pip install gunicorn psycopg2-binary

python manage.py makemigrations

python manage.py migrate
````

https://docs.djangoproject.com/en/3.0/topics/migrations/

# OpenAPI DOC

http://BASE_URL/openapi?format=openapi-json

# create super user

python manage.py createsuperuser


# static files

see https://docs.djangoproject.com/en/3.0/howto/static-files/deployment

````
$ python manage.py  collectstatic
````

# locale

django-admin makemessages -l es
django-admin compilemessages

# dev server

python manage.py runserver

# kill debug process

sudo lsof -t -i tcp:8000 | xargs kill -9

# queue listener

python manage.py listener

# start Celery worker process

````
celery -A backend worker -l info
````
# start show model feed command

````
python manage.py do_model_snapshot SUMMIT_ID -o=OPERATION_MODE
````

**OPERATION_MODE**:
- **download**: fetch the show model from summit-api to a local folder
- **upload**: upload all the json files in the local folder to S3
- **full**: download + upload


# run job

python manage.py runjob entities_updates_purge_job