from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominioaldia.settings')

app = Celery('condominioaldia', broker='amqp://',broker_url = 'amqp://')

#CELERY BEAT
app.conf.beat_schedule = {
    # 'print-time-every-30-seconds': {
    #     'task': 'condominioaldia_app.tasks.print_time',
    #     'schedule': 30.0
    #     #'args': (16, 16)
    # },
    'add-every-monday-morning': {
        'task': 'condominioaldia_app.tasks.delete_expired_confirmations_beat',
        'schedule': crontab(hour=4, minute=0)
    },
    'add-every-monday-morning': {
        'task': 'condominioaldia_app.tasks.update_condo_status_beat',
        'schedule': crontab(hour=4, minute=15)
    }
}
app.conf.timezone = 'UTC'
#########
# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


