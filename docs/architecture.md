# Adme Ops Screen — Architecture (living document)

**Version 2.0** · Supersedes `Adme_OpsScreen_Dev_Plan.docx` (v1.0) for the
**Presentation layer** and for every **open decision** listed here.
Derived from `Adme_RD_Requirement_Document.pdf` (v1.2).

The `.docx` is kept as the historical v1.0. Where the two disagree, **this file
wins**. Module list, MySQL schema (21 tables), user stories, Definition of Done,
and the phased build order in the `.docx` are still authoritative — read it too.

---

## 1. What changed vs the `.docx`

| Area | `.docx` v1.0 | Now |
|------|--------------|-----|
| Frontend | React JS (Vite), React Router, Recharts — web only | **React Native via Expo** (`react-native-web` for web) — one codebase → web + iOS + Android. See [ADR 0001](adr/0001-react-native-frontend.md). |
| Open decisions | left as "refine during implementation" | resolved below (§4–§12) or captured as ADRs |
| Scaffold defects | present (red CI, no JWT role, etc.) | fixed — see §13 |

---

## 2. System overview

One internal platform, one login, role-based screens for six roles
(merchant, consumer, admin, driver, hardware, super_admin). One Django/DRF
backend, one MySQL database, Redis + Celery for scheduled/async work. Nothing is
a standalone third-party app.

```
                 ┌─────────────────────────────────────────────┐
   iOS / Android │   Expo app  (React Native + react-native-web) │  web (static export)
      binaries   │   one codebase, role-based routing            │  behind Nginx / CDN
                 └───────────────────────┬─────────────────────┘
                                         │ HTTPS  /api/v1/*  (JWT, role in token)
                 ┌───────────────────────▼─────────────────────┐
                 │  Nginx  →  Gunicorn/Uvicorn  →  Django + DRF  │
                 │  8 apps: accounts, merchants, consumers,       │
                 │  rickshaws, reports, notifications, analytics, │
                 │  admin_ops                                     │
                 └───────┬───────────────┬───────────────┬──────┘
                         │               │               │
                   ┌─────▼────┐    ┌──────▼─────┐   ┌─────▼──────┐
                   │ MySQL 8  │    │ Redis      │   │ Celery      │
                   │ (SoR)    │    │ cache+broker│  │ worker+beat │
                   └──────────┘    └────────────┘   └─────────────┘
                         │
        ┌────────────────┼──────────────────────────┐
        │                │                          │
  Object storage   WhatsApp Business API        Maps API
  (reports, KYC)   Email / SMTP                 (Google or Mapbox)
```

### Layer 1 — Presentation (Expo app)

- **One codebase, three targets.** `react-native-web` renders the web Ops Screen
  (built with `expo export -p web`, served as static files by Nginx/CDN). The
  same source ships to iOS/Android via **EAS Build**.
- **Routing** is file-based (**Expo Router**) with one route group per role
  (`app/(merchant)`, `app/(consumer)`, …). Each group's `_layout.tsx` is the
  role guard — it reads `role` from the JWT and redirects out if the role isn't
  allowed. This is Story **CORE-1**.
- **Realistic target per role:** merchant / admin / super_admin → mostly web;
  consumer / driver → mostly mobile; hardware → the `device` screen build.
  All from the same repo.
- **Native capabilities now in scope:** real camera QR scanning (`expo-camera`,
  Story CON-1), device GPS for near-me (Story CON-2) and driver telemetry, Expo
  push notifications (an extra channel alongside WhatsApp/Email), deep links
  (`adme://offer/<code>`).

### Layers 2–4

Unchanged from the `.docx`: DRF API gateway (versioned `/api/v1`, JWT, per-endpoint
role permission, throttling, request logging) → modular Django apps → MySQL +
Redis + Celery + object storage + external gateways.

---

## 3. App dependency direction

Keep imports flowing one way; do not create cycles.

```
accounts  ◄── merchants ◄── consumers
   ▲            ▲   ▲          ▲
   │            │   └── rickshaws
   │            │
   └──────── analytics  (reads merchants + consumers + rickshaws)
   └──────── reports    (reads merchants; triggers notifications)
   └──────── notifications (reads any; sends WhatsApp/Email)
   └──────── admin_ops  (AuditLog; read-only dashboards over everything)
common/  — no app imports; imported by all (permissions, audit mixin, pagination, health)
```

---

## 4. Role → access matrix (authoritative)

| Resource | merchant | consumer | admin | driver | hardware | super_admin |
|---|---|---|---|---|---|---|
| `auth/login`, `auth/me` | ✔ | ✔ | ✔ | ✔ | ✔ (device creds) | ✔ |
| `merchants/merchants/apply` | ✔ (public application) | – | – | – | – | – |
| `accounts/users` | – | – | – | – | – | CRUD |
| `merchants/merchants` | read own | – | **read** | – | – | CRUD |
| `merchants/plans`, `categories` | read | read | **read** | – | – | CRUD |
| `merchants/area-mappings` | read own | – | **read** | – | – | CRUD |
| `merchants/campaigns`, `offers` | CRUD own | read (scan) | **read** | – | – | CRUD |
| `merchants/campaign-metrics` | read own | – | **read** | – | – | read (written by Celery) |
| `merchants/reports` | read own | – | **read** | – | – | read |
| `offers/match`, `redemptions/{id}/approve` | own | – | – | – | – | ✔ |
| `consumers/*` | – | own | **read** | – | – | CRUD |
| `offers/scan`, `offers/near-me` | – | ✔ | – | – | – | ✔ |
| `rickshaws/drivers` (+ `kyc`) | – | – | **read + approve** | own submit | – | CRUD |
| `rickshaws/rickshaws`, `hardware` | – | – | **read** | read own | – | CRUD |
| `rickshaws/{id}/gps`, `hardware/{id}/heartbeat` | – | – | – | own | **device creds** | ✔ |
| `rickshaws/gps-pings`, `uptime-logs` | – | – | **read** | – | – | read |
| `analytics/platform-overview` | – | – | **read** | – | – | read |
| `admin-ops/audit-logs` | – | – | **read** | – | – | read |
| `admin-ops/merchant-verifications` | – | – | **read + approve/reject** | – | – | CRUD |

**Rule:** `admin` is strictly read-only platform-wide. Merchant applications
are submitted publicly and reviewed through the admin verification queue. Any ViewSet an
`admin` can reach that also has write methods must use
`common.permissions.IsSuperAdminOrReadOnlyAdmin` (or `ReadOnly | IsSuperAdmin`).
`super_admin` bypasses all read-only restrictions (RD §6).

---

## 5. API URL scheme (reconciles `.docx` §7 with the router reality)

Routers nest under the app prefix, so the real paths are:

| `.docx` §7 shorthand | Actual path |
|---|---|
| `POST /auth/login` | `POST /api/v1/auth/login/` → `{access, refresh, role, name, user_id}` |
| — | `GET /api/v1/auth/me/` → current user + role (client bootstrap) |
| `GET/POST /merchants/` | `/api/v1/merchants/merchants/` |
| `GET /merchants/{id}/dashboard/` | `/api/v1/merchants/merchants/{id}/dashboard/` (custom `@action`, TODO MER-3) |
| `GET /merchants/{id}/reports/` | `/api/v1/merchants/reports/?merchant={id}` |
| `POST /offers/scan/` | `/api/v1/consumers/redemptions/scan/` — consumer, CON-1 |
| `POST /offers/match/` | `/api/v1/consumers/redemptions/match/` — merchant, MER-5 (RD 2.6) |
| `POST /redemptions/{id}/approve/` | `/api/v1/consumers/redemptions/{id}/approve/` — merchant, MER-5 (RD 2.7) |
| — | `/api/v1/consumers/redemptions/{id}/reject/` — merchant |
| — | `/api/v1/consumers/redemptions/me/` — consumer's own history |
| — | `/api/v1/consumers/consumers/me/` — consumer profile + points (CON-4) |
| `GET /offers/near-me/?radius=1km` | `/api/v1/merchants/offers/near-me/?lat=&lng=&radius_km=` (0.5/1/3) — consumer, CON-2 |
| `GET /admin/overview/` | `/api/v1/analytics/platform-overview/` (live rickshaws, redemptions, advertiser count) |
| — | `/api/v1/analytics/advertisers/` — advertiser directory: campaign status + spend (RD 4.3) |
| — | `/api/v1/analytics/live-fleet/` — active rickshaws + latest position + `is_live` (RD 4.1) |
| `POST /rickshaws/{id}/gps/` | `/api/v1/rickshaws/rickshaws/{id}/gps/` (TODO RIK-2) |
| `POST /hardware/{id}/heartbeat/` | `/api/v1/rickshaws/hardware/{id}/heartbeat/` |
| `POST /drivers/{id}/kyc/` | `/api/v1/rickshaws/drivers/{id}/kyc/` + `.../approve/` |

Custom actions stay **flat verbs** on the resource via `@action`. Full generated
schema: `GET /api/v1/schema/`; Swagger UI: `GET /api/v1/docs/`.

---

## 6. Auth & sessions

- **Login identifier** may be username, email, or phone (RD CORE-1) —
  `apps.accounts.auth.EmailOrPhoneBackend`.
- **JWT** carries `role`, `name`, `user_id` (`AdmeTokenObtainPairSerializer`) so
  the client redirects without a second call. Access token **30 min**, refresh
  **7 days**, rotation + blacklist on.
- **CORE-2 "deactivate = immediate lockout":** on `is_active → False` the user's
  outstanding refresh tokens are blacklisted; the live access token then dies
  within ≤30 min. Documented trade-off; tighten access lifetime further if the
  business needs true-instant.
- **Client token storage:** `expo-secure-store` on native, `localStorage` on web
  (wrapped in `src/lib/storage.ts`).
- **Device (hardware) auth:** per-unit API key, `X-Device-Key` header — see
  [ADR 0003](adr/0003-device-auth.md).
- **Password reset / invite flow:** TODO, Phase 1 — email link via the
  notifications app.
- **NearMe customer signup:** `POST /api/v1/auth/signup/request-otp/` creates a
  short-lived hashed email OTP challenge. `POST /api/v1/auth/signup/verify-otp/`
  verifies it, creates the consumer profile, and returns the normal JWT login
  payload. Customer data is visible to admins through
  `GET /api/v1/consumers/consumers/`.

---

## 7. Geospatial — "Near Me" (Story CON-2)

- **v1:** bounding-box prefilter on `merchants.latitude/longitude` (add a
  composite index) then haversine in Python; sort by distance. Radius options
  500 m / 1 km / 3 km.
- **Upgrade path:** MySQL 8 `POINT` column + `SPATIAL INDEX` +
  `ST_Distance_Sphere`. Switch when merchant count or request rate makes the
  prefilter slow.
- `consumers.Redemption.scan_latitude/longitude` already store scan location.

---

## 8. Real-time dashboards (Story ADM-1, RIK-2)

- **v1:** client polling — 10–15 s for the fleet map and the admin overview
  (matches RIK-2's stated refresh). No WebSockets.
- `ASGI_APPLICATION` is wired but `channels` is **not** installed; add it only
  when polling proves insufficient.

---

## 9. Files & object storage (Stories MER-2, RIK-1)

- **dev / CI:** local `MEDIA_ROOT`.
- **staging / prod:** `USE_S3=True` → `django-storages` S3 backend, private
  bucket, short-lived signed URLs. See [ADR 0002](adr/0002-object-storage.md).
- Reports: `Report.file_url` holds the storage key/URL; the merchant gets a
  signed link by email + WhatsApp.
- KYC docs (`Driver.id_proof_url` etc.): must become real uploads
  (`FileField` / multipart `POST .../kyc/`), stored private, access-controlled to
  admin + super_admin + the owning driver.

---

## 10. GPS ingestion & retention (Stories RIK-2, RIK-4; Dev Plan Phase 8)

- `POST /rickshaws/{id}/gps/` — lightweight create, device-auth, accepts a single
  ping or a small batch. No heavy serialization; this is the highest-frequency
  endpoint. Its own throttle scope (`device_ingest`).
- **Retention:** keep raw `gps_pings` **14 days**, then delete (a nightly Celery
  task). The live map only needs the latest ping per rickshaw; historical
  route analysis works off a downsampled table if needed later.
- Heartbeat sweep (`apps.rickshaws.tasks.check_heartbeats`, every 5 min) flips a
  unit `offline` after 15 min of silence and writes an `uptime_logs` row; uptime
  % feeds ad-impression auditing.

---

## 11. Analytics semantics (Stories MER-2, MER-3)

Define these before implementing the report/charts:

- **Ad Views (Est.)** = `Σ (unit_uptime_minutes_in_period × plays_per_minute)`
  for units in the campaign's area mapping, where `plays_per_minute` is a
  configured constant (system config, super_admin). It is an **estimate** — label
  it as such (RD 2.2).
- **Store Visit confirmed** = a GPS fix within **150 m** of the merchant's stored
  location, within **24 h** of the scan, dwell ≥ **2 min**. Constants are system
  config.
- **Redemption pie chart** buckets: by `offer.category` **or** by time slot —
  slots = `[06–12, 12–17, 17–21, 21–06]` local.
- `campaign_metrics` is a **nightly rollup** (`rollup_campaign_metrics`); the
  weekly report and all dashboards read the rollup, never raw events.

---

## 12. State machines

### Offer / redemption (Stories CON-1, MER-5, CON-4)

```
Redemption.match_status:     pending ──match ok──► matched ──► (approval)
                                   └──mismatch──► mismatched  (terminal, retry = new row)

Redemption.approval_status:  pending ──merchant Approve──► approved  (points/discount applied,
                                   └──merchant Reject───► rejected    approved_by/at stamped)

Offer.status:                active ──all uses consumed / expiry──► redeemed | expired
```

Transitions allowed only in that order; `approve` requires `match_status == matched`
and the caller to own the merchant (or be super_admin). Every transition writes an
`AuditLog` row.

### Driver KYC (Story RIK-1)

```
kyc_status: pending ──review──► approved | rejected(+reason)
Rickshaw.status can become `active` only when its driver's kyc_status == approved.
```

---

## 13. Scaffold fixes applied (was blocking Phase 0/1)

| Ref | Fix |
|---|---|
| A2 | `adme_backend/tests/test_smoke.py` — CI `pytest` now green with real assertions |
| A3 | `adme_backend/setup.cfg` `[flake8]` (`max-line-length = 120`, ignores) |
| A4 | `AdmeTokenObtainPairSerializer/View` put `role` in the JWT + response; `GET /auth/me/` added |
| A5 | `apps.notifications.urls` now included in `config/urls.py` |
| A6 | `EmailOrPhoneBackend` — login by username / email / phone |
| A7 | `token_blacklist` app + blacklist-on-deactivate in `UserViewSet`; access lifetime 30 min |
| A8 | backend `.env.example` gains `CORS_ALLOWED_ORIGINS` (Expo origins) + S3 vars |
| B6 | `common/audit.py::AuditLogMixin` — the single audit mechanism; applied to `accounts` + `merchants` write ViewSets, extend to the rest per phase |
| B7 | `common.permissions.IsSuperAdminOrReadOnlyAdmin`; applied to `Merchant/AreaMapping/CampaignMetric` |
| B9 | `drf-spectacular` — `/api/v1/schema/`, `/api/v1/docs/` |
| B10 | `CELERY_BEAT_SCHEDULE` in `settings/base.py` (weekly report, daily expiry, 5-min heartbeat, nightly rollup) + task stubs `apps/{merchants,rickshaws}/tasks.py` |
| B16 | DRF throttling scopes (`login`, `device_ingest`), `LOGGING`, `/healthz/`, `prod.py` hardening (HSTS, secret guard), `.dockerignore`, `seed` command |

**Done beyond scaffold (Phase 1 + MER-3/ADM-1 slice):**
`GET /api/v1/auth/me/` returns the role's linked profile id
(`merchant_id`/`consumer_id`/`driver_id`);
`GET /api/v1/merchants/merchants/{id}/dashboard/` (Story MER-3) — totals +
daily time-series + redemption breakdown, owner-or-admin only, via
`apps.analytics.services`; all three analytics endpoints (`platform-overview`, `advertisers`, `live-fleet`)
locked to admin/super_admin (Story ADM-1). "Live rickshaw" = active **and** a
GPS ping within `LIVE_RICKSHAW_WINDOW` (15 min). `seed` produces a populated
demo merchant + a 3-rickshaw fleet (2 live, 1 stale) so every dashboard renders
immediately. Frontend: working login (email/phone/username), session restore +
`/me` hydration, `RoleGuard` route groups, Merchant dashboard (KPI row + SVG
line/bar charts), **Admin dashboard** — Overview / Advertisers / Live Fleet
sections (`app/(admin)/{index,advertisers,fleet}.tsx`, 10–15s polling, strictly
read-only), shared `DashboardHeader` with logout.

**Redemption flow (Phase 3) — DONE.** `apps.consumers.services` holds the whole
transaction so side effects can't drift: `scan_offer` (CON-1, +5 Adme pts),
`match_offer` (MER-5 / RD 2.6), `approve_redemption` (RD 2.7 — offer→redeemed,
+10 merchant loyalty pts, +20 Adme pts, `merchant.total_redemptions`++, today's
`CampaignMetric.offers_redeemed`++), `reject_redemption`, `consumer_profile`
(CON-4). `nearby_offers` (CON-2) = bbox prefilter + haversine, radius ∈
{0.5,1,3}. Every `Redemption` list is role-scoped (consumer→own, merchant→own
store, admin→all); raw CRUD on redemptions is super_admin-only.
`AuditLogMixin` now also wired into `consumers` + `rickshaws` ViewSets; the flow
`@action`s call `write_audit`.

**Still TODO (tracked, not blocking):** `AuditLogMixin` on `admin_ops` (it is
read-only, low priority); weekly report generation + WhatsApp/Email delivery
(MER-2/MER-4 tasks are stubs); GPS-ingest endpoint + uptime-% (RIK-2/RIK-4);
KYC upload as `FileField` (RIK-1); Super Admin config model (SUP-2);
password-reset; CD pipeline.

---

## 14. Non-functional requirements (new — absent from RD & `.docx`)

| Topic | v1 target |
|---|---|
| Concurrency | ≤ 2 000 rickshaws, ≤ 1 GPS ping / rickshaw / 10 s (~200 req/s peak); ≤ 50 concurrent ops users |
| Latency | dashboard reads p95 < 500 ms; GPS ingest p95 < 100 ms |
| Availability | 99.5 % monthly for the API; scheduled jobs must be idempotent and safe to re-run |
| Data retention | raw `gps_pings` 14 d; `audit_logs` 2 y; reports 2 y; KYC docs for contract term + 1 y |
| Backups | managed MySQL automated daily snapshot + 7-day PITR; object storage versioning on |
| PII / KYC | KYC docs private, access = admin/super_admin/owner; access logged; encrypted at rest |
| Environments | `dev` (local docker), `staging` (UAT, prod-like), `prod` — settings via `config.settings.{dev,prod}` + env vars |
| Deploy topology | Nginx → Gunicorn (N workers) ; separate Celery worker + beat ; managed MySQL ; managed Redis ; object storage ; web static export on CDN |
| Observability | structured logs to stdout; `/healthz/` for probes; add Sentry (or equivalent) DSN in staging/prod |
| Rate limiting | DRF `ScopedRateThrottle` — `login` 10/min, `device_ingest` 120/min, authed default 1000/h |
| CI/CD | CI = flake8 + pytest (backend), `expo export -p web` + eslint + tsc (frontend). **CD is TODO**: migrate-gate + image publish + deploy. |

---

## 15. Frontend stack (see also `adme_frontend/README.md`)

| Concern | Choice |
|---|---|
| Runtime | React Native via **Expo SDK (latest)** + `react-native-web` |
| Routing | **Expo Router** (file-based), one route group per role |
| Server state | **RTK Query** slices per Django app (`src/api/*`) |
| Client state | Redux Toolkit (`src/store`, `auth` slice) |
| HTTP | `axios` base client; token from `src/lib/storage` (secure-store / localStorage) |
| Charts | **react-native-svg**, hand-rolled (`src/components/charts/`) for the v1 dashboard — small, web-safe under `expo export`. `victory-native` v36 (the web-compatible line) can be added later for richer charts. Not Recharts (DOM-only). |
| Maps | **react-native-maps** or **@rnmapbox/maps** — [ADR 0005](adr/0005-map-provider.md) |
| QR scan | **expo-camera** (native barcodes); web via its getUserMedia shim |
| Styling | **NativeWind** (Tailwind syntax, all three targets) |
| Forms | `react-hook-form` |
| Push | `expo-notifications` |
| Build | `expo start` (dev) · `expo export -p web` (web) · **EAS Build** (iOS/Android) |
| Lint/type | ESLint (`eslint-config-expo`) + Prettier + `tsc --noEmit` |

### Folder layout

```
adme_frontend/
  app/                      # Expo Router — mirrors RD roles 1:1
    _layout.tsx             #   providers (Redux, RTK Query, SafeArea) + auth bootstrap
    index.tsx               #   redirect to login or role home
    login.tsx
    (merchant)/  _layout.tsx  index.tsx campaigns.tsx reports.tsx approve.tsx
    (consumer)/  _layout.tsx  index.tsx scan.tsx near-me.tsx profile.tsx
    (admin)/     _layout.tsx  index.tsx                        # read-only
    (rickshaw)/  _layout.tsx  kyc.tsx fleet-map.tsx device.tsx
    (superadmin)/_layout.tsx  users.tsx plans.tsx config.tsx audit-log.tsx
  src/
    api/        # RTK Query: baseApi + authApi, merchantApi, consumerApi, ...
    store/      # configureStore + auth slice
    components/ # shared RN UI: Screen, Card, DataTable, Chart, MapView, RoleBadge
    lib/        # storage, jwt (decode role), roleHome()
    theme/      # NativeWind config + tokens
  app.config.ts  eas.json  metro.config.js  babel.config.js  tsconfig.json
```

Env vars: `EXPO_PUBLIC_API_BASE_URL`, `EXPO_PUBLIC_MAPS_API_KEY`.
Rule of thumb (unchanged): **one Django app ⇄ one route group ⇄ one `src/api` slice.**

### Dev-plan phase deltas

- **Phase 0** — Expo skeleton (Expo Router + RTK Query + NativeWind) running on
  web + one simulator; `eas init`. `docker-compose` frontend service is now
  `expo` (Metro web). Frontend CI: `expo export -p web` + `eslint` + `tsc`.
- **Phase 1** — role redirect via route groups; token in `expo-secure-store`;
  consume `/auth/me/`.
- **Phase 3** — CON-1 scan via `expo-camera`, payload per §12 / QR spec below.
- **Phase 5** — charts via `victory-native`.
- **Phase 6** — fleet map via the ADR 0005 provider; plan internal distribution
  (not public stores) for the driver + hardware builds.

### QR payload spec (Story CON-1)

QR encodes a deep link: `adme://offer/<offer_code>` (and an `https://` universal
link fallback). `offer_code` is the existing unique `Offer.offer_code`. Scanning
opens the app to the scan screen pre-filled; manual entry accepts the bare code.
Codes do not rotate in v1; offer expiry is enforced server-side.
