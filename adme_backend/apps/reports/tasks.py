"""
Celery tasks for weekly merchant reporting (RD 2.1, Story MER-2, Dev Plan Phase 4).

generate_weekly_reports:
    - Runs on a weekly schedule via Celery Beat (register in Django admin
      under Periodic Tasks, or in CELERY_BEAT_SCHEDULE).
    - For every active merchant: aggregate apps.merchants.models.CampaignMetric
      for the period into the fixed Campaign/Duration/Ad Views/QR Scans/
      Offer Saved/Store Visits/Offer Redeemed columns (RD 2.2).
    - Write a locked/read-only .xlsx with openpyxl (set sheet protection).
    - Upload to object storage, create an apps.merchants.models.Report row.
    - Trigger apps.notifications.tasks.send_report(report_id).
"""
from celery import shared_task


@shared_task
def generate_weekly_reports():
    # TODO: implement per the docstring above.
    raise NotImplementedError
