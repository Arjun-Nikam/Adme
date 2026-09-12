# ADR 0002 — Object storage for reports & KYC documents

- **Status:** Accepted
- **Date:** 2026-08-30

## Context

RD 2.1 (weekly Excel reports, delivered by signed download link) and RD 5 (KYC
docs: license, RC, ID proof) both need durable file storage. The `.docx` mentions
"S3-compatible object storage… signed URL" but the scaffold had no storage
backend, `Report.file_url` was a bare `URLField`, and KYC fields were URL strings
with no upload path.

## Decision

- **dev / CI:** Django's default filesystem storage under `MEDIA_ROOT`.
- **staging / prod:** `USE_S3=True` → `django-storages` S3 backend (`boto3`),
  **private** bucket, `AWS_QUERYSTRING_AUTH=True` so every link is a short-lived
  signed URL. `AWS_S3_ENDPOINT_URL` lets us point at any S3-compatible provider.
- KYC documents become real uploads: `FileField` on `Driver`, multipart
  `POST /api/v1/rickshaws/drivers/{id}/kyc/`. Stored private; download only for
  `admin`, `super_admin`, and the owning `driver`; each access is written to
  `AuditLog`.
- Reports: Celery writes the `.xlsx` to storage, saves the key on
  `Report.file_url`, and the notification carries a freshly signed URL
  (regenerated on each `GET /reports/{id}/` too, since signatures expire).

## Consequences

- New deps: `django-storages`, `boto3` (in `requirements.txt`).
- New env vars: `USE_S3`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`,
  `AWS_S3_REGION_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.
- Object storage versioning should be enabled for reports + KYC (NFR §14).
- Retention: KYC kept for contract term + 1 year, then purged.
