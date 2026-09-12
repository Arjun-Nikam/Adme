import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("adme")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# The recurring schedule lives in config/settings/base.py::CELERY_BEAT_SCHEDULE
# (weekly merchant reports, daily plan-expiry alerts, heartbeat sweep, nightly
# metrics rollup). CELERY_BEAT_SCHEDULER is django_celery_beat's DatabaseScheduler,
# so ops can adjust timings in the Django admin without a deploy.
