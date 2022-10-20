import os

from .celery import celery_app
from dotenv import load_dotenv

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
env = os.getenv('ENV')
filename = '.env'
if env:
    filename = '{filename}.{env}'.format(filename=filename, env=env)

ENV_FILE = os.path.join(CURRENT_PATH, filename)
load_dotenv(ENV_FILE)

__all__ = ['celery_app']
