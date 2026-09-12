"""
Celery tasks for WhatsApp/Email delivery.

send_expiry_alerts:
    - Runs daily. For every Merchant whose contract_expiry_date is exactly
      5 days out, send a WhatsApp message and log a Notification row
      (RD 2.5, Story MER-4).

send_report(report_id):
    - Sends the generated Excel report as an Email attachment AND via
      WhatsApp Business API with a download link (RD 2.1, Story MER-2).
    - Retries on failure; updates Report.sent_via_email / sent_via_whatsapp.
"""
from celery import shared_task


@shared_task
def send_expiry_alerts():
    # TODO: implement per the docstring above.
    raise NotImplementedError


@shared_task
def send_report(report_id: int):
    # TODO: implement per the docstring above.
    raise NotImplementedError
