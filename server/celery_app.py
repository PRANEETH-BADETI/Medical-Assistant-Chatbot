# server/celery_app.py
from celery import Celery
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery = Celery(
    __name__,
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# where to find our tasks
celery.conf.imports = (
    'tasks',
)

celery.conf.update(
    task_track_started=True,
)