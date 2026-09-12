# Adme — Ops Screen Module

Monorepo for Adme's internal Ops Screen platform: Merchant, Consumer, Admin,
Auto Rickshaw (Driver + Hardware), and Super Admin — one system, role-based
screens, one MySQL database.

- **Backend:** `adme_backend/` — Python, Django + Django REST Framework, Celery, MySQL
- **Frontend:** `adme_frontend/` — **React Native via Expo** (`react-native-web`
  for web), Expo Router, Redux Toolkit + RTK Query. One codebase → web + iOS +
  Android. See [ADR 0001](docs/adr/0001-react-native-frontend.md).
- **Docs:** `docs/` — **start with [`docs/architecture.md`](docs/architecture.md)**
  (living doc; supersedes the frontend + open-decision parts of the `.docx`), then
  the ADRs in `docs/adr/`, then the original `.docx` for schema / user stories /
  phased plan.

## Quick start (Docker — backend + infra)

```bash
cp adme_backend/.env.example adme_backend/.env
docker compose up --build          # db, redis, backend, celery worker + beat, expo web
```

- Backend API: http://localhost:8000/api/v1/
- API docs (Swagger): http://localhost:8000/api/v1/docs/
- Django admin: http://localhost:8000/admin/
- Health probe: http://localhost:8000/healthz/
- Frontend (Expo web): http://localhost:8081/

Seed local users (one per role, password `adme-dev-1234`):

```bash
docker compose exec backend python manage.py seed
```

### Frontend for iOS / Android

Run Expo on the host (simulators/emulators aren't reachable from the container):

```bash
cd adme_frontend
cp .env.example .env
npm install
npx expo start          # press i / a for iOS / Android, w for web
```

## Repo layout

```
adme-platform/
  adme_backend/       # Django project — one app per RD module (see its README)
  adme_frontend/      # Expo app — one route group per RD role (see its README)
  docs/
    architecture.md   # <- living architecture doc, start here
    adr/              # decision records (frontend, storage, device auth, ...)
    Adme_OpsScreen_Dev_Plan.docx   # historical v1.0 — schema, stories, phased plan
    Adme_RD_Requirement_Document.pdf
  docker-compose.yml
  .github/workflows/  # CI: backend flake8+pytest, frontend expo export + eslint + tsc
```

## Status of this base setup

Scaffold, plus the Phase-0 readiness fixes from `docs/architecture.md` §13:
- Backend: `manage.py check` + `flake8` + `pytest` are green; models migrate cleanly;
  JWT carries `role`; `/auth/me/`, `/healthz/`, `/api/v1/docs/` live; audit mixin,
  role→permission matrix, Celery beat schedule, throttling in place.
- Frontend: Expo app skeleton — Expo Router role groups, role guard, RTK Query
  base, `expo export -p web` + `eslint` + `tsc` pass.
- Business logic (offer matching, report generation, WhatsApp/email delivery, GPS
  map, KYC review, analytics aggregation) is stubbed with `TODO`s pointing at the
  story ID — see the `.docx` §8 for stories, §9 for build order, and
  `architecture.md` §13 for what's still TODO.

## Contributing (for interns / new devs)

1. Read `docs/architecture.md`, then the relevant ADR(s), then the `.docx`.
2. Pick up a story by its ID (e.g. `MER-2`) from the project board.
3. One story ≈ one Django app change + one matching Expo route group + one
   `src/api` slice.
4. Open a PR; CI must pass before merge.
5. Anything that creates/updates/deletes/approves data goes through
   `common.audit.AuditLogMixin` (or `self.write_audit(...)`), never ad-hoc.

## License

Internal use only — Adme proprietary.
