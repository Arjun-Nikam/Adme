# ADR 0003 — Hardware device authentication

- **Status:** Accepted
- **Date:** 2026-08-30

## Context

Hardware display units push high-frequency GPS telemetry
(`POST /rickshaws/{id}/gps/`) and connectivity heartbeats
(`POST /hardware/{id}/heartbeat/`). These are unattended devices — no human
login, no interactive token refresh. The scaffold had a `hardware` user role but
no credential scheme, so these endpoints were effectively unauthenticated.

## Decision

**Per-unit API key.**

- `HardwareUnit` gains `api_key` (opaque random, 40+ chars, hashed at rest) and
  `api_key_issued_at`.
- Devices send `X-Device-Key: <key>` on every request. A DRF authentication
  class `DeviceKeyAuthentication` resolves it to the `HardwareUnit` and its
  linked `Rickshaw`; a `IsProvisionedDevice` permission gates the ingest
  endpoints.
- Keys are issued/rotated by `super_admin` from the Super Admin config screen
  (Story SUP-2); rotation writes `AuditLog`.
- Ingest endpoints get their own throttle scope (`device_ingest`, 120/min) and
  do **not** accept JWT auth — separation of paths.

## Consequences

- Migration adds two columns to `hardware_units`.
- The provisioning flow (generate key → flash to device) is a Phase 6 task.
- Compromised key = revoke + reissue for that one unit; blast radius is a single
  screen.
- Rejected: machine JWT (needs a refresh story on the device); mTLS (operationally
  heavy for a fleet of cheap Android screens).
