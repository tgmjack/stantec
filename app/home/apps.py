import sys

from django.apps import AppConfig
from dotenv import load_dotenv


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'

    def ready(self):
        pass


