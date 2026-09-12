# Adme Backend (Django + DRF)

Ops Screen Module API. One Django app per RD module — see `apps/`.
Architecture + open decisions: `../docs/architecture.md` and `../docs/adr/`.

## Local setup

```bash
cp .env.example .env          # fill in DB creds etc.
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py seed         # dev users (one per role) + categories + a plan
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Or with Docker (recommended, matches CI):

```bash
docker compose up --build
```

- API root: http://localhost:8000/api/v1/
- Swagger UI: http://localhost:8000/api/v1/docs/  ·  schema: `/api/v1/schema/`
- Health: http://localhost:8000/healthz/

## Auth

- `POST /api/v1/auth/login/` — identifier may be **username, email, or phone**
  (`apps.accounts.auth.EmailOrPhoneBackend`); returns
  `{access, refresh, role, name, user_id}`. The JWT itself carries `role`.
- `POST /api/v1/auth/refresh/` — rotate; `GET /api/v1/auth/me/` — current user.
- Deactivating a user (`is_active=False`) blacklists their refresh tokens; the
  live access token expires within 30 min (see `architecture.md` §6).

## Where things live

| Module (RD section)         | Django app            |
|------------------------------|------------------------|
| Auth / roles (1)             | `apps.accounts`        |
| Merchant (2)                 | `apps.merchants`       |
| Consumer (3)                 | `apps.consumers`       |
| Admin (4)                    | `apps.analytics` (read) + `apps.admin_ops` |
| Auto Rickshaw (5)            | `apps.rickshaws`       |
| Super Admin (6)              | all apps (full CRUD) + `apps.admin_ops` |
| Weekly report generation     | `apps.reports`         |
| WhatsApp / Email delivery    | `apps.notifications`   |

Full schema + story references: `../docs/Adme_OpsScreen_Dev_Plan.docx`.
Role→permission matrix, API URL scheme, state machines: `../docs/architecture.md`.

## Conventions

- Every DRF view sets `permission_classes` explicitly. `admin` is read-only
  platform-wide — use `common.permissions.IsSuperAdminOrReadOnlyAdmin` (or
  `ReadOnly | IsSuperAdmin`) on any write-capable ViewSet an `admin` can reach.
- Auditing goes through `common.audit.AuditLogMixin` (add it to the ViewSet) or
  `self.write_audit(action, instance, details=None)` for custom `@action`s.
  Never call `AuditLog.objects.create()` ad hoc.
- Scheduled jobs are declared in `config/settings/base.py::CELERY_BEAT_SCHEDULE`
  and run under django-celery-beat's DatabaseScheduler.
- Run `black .` and `flake8` before opening a PR (`setup.cfg` holds both configs).
- New tests live next to their app or in `tests/`; `pytest` must stay green.
