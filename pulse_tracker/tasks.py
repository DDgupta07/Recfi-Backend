import time
from celery import shared_task

from utils.helper import get_percentage_change


@shared_task()
def monitor_percentage_change():
    start_time = time.time()
    get_percentage_change()
    end_time = time.time()
    return f"Time taken to complete pulse tracker notification: {end_time - start_time} seconds."
