import os

from celery import Celery
from celery.schedules import crontab


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Recifi.settings")

app = Celery("Recifi")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "pulse_tracker_notifications": {
        "task": "pulse_tracker.tasks.monitor_percentage_change",
        "schedule": 60.0,
    },
    "Recifi_wallets_24h_percentage_change_hourly": {
        "task": "trade.tasks.Recifi_wallets_24h_percentage_change",
        "schedule": crontab(minute=0),
    },
    "Recifi_notifications": {
        "task": "trade.tasks.Recifi_alerts",
        "schedule": crontab(minute=10, hour="*"),
    },
    "update_historical_price_of_recifi": {
        "task": "trade.tasks.update_historical_price",
        "schedule": crontab(minute=3, hour=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
