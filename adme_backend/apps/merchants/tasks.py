"""
Celery tasks for the Merchant module (Dev Plan Phase 4).

rollup_campaign_metrics:
    - Runs nightly (CELERY_BEAT_SCHEDULE).
    - Aggregates the day's raw events (ad views, QR scans, offers saved,
      store visits, redemptions) into one CampaignMetric row per active
      campaign for that date (RD 2.2). Idempotent per (campaign, date).
    - The weekly report job (apps.reports.tasks.generate_weekly_reports)
      reads these rows, never raw events.
"""
from celery import shared_task


@shared_task
def rollup_campaign_metrics():
    # TODO (Dev Plan Phase 4): implement per the docstring above.
    raise NotImplementedError
