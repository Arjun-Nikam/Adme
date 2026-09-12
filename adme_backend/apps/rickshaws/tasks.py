"""
Celery tasks for the Auto Rickshaw module (RD 5, Stories RIK-4).

check_heartbeats:
    - Runs every 5 minutes (CELERY_BEAT_SCHEDULE).
    - Any HardwareUnit whose last_heartbeat_at is older than
      HEARTBEAT_OFFLINE_AFTER is flipped to status=offline and an
      UptimeLog(is_online=False) row is written.
    - Feeds the uptime % used for ad-impression auditing (RD 5).
"""
from datetime import timedelta

from celery import shared_task

HEARTBEAT_OFFLINE_AFTER = timedelta(minutes=15)


@shared_task
def check_heartbeats():
    # TODO (Story RIK-4): implement per the docstring above.
    raise NotImplementedError
