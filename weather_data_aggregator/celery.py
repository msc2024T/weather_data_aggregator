import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "weather_data_aggregator.settings")

app = Celery("weather_data_aggregator")

# Load settings with CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py files in apps
app.autodiscover_tasks()
