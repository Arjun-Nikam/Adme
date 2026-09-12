# ADR 0004 — WhatsApp Business API provider

- **Status:** Proposed (needs a commercial call before Phase 4)
- **Date:** 2026-08-30

## Context

RD 2.1 (weekly report link) and RD 2.5 (plan-expiry alert, 5 days out) send
templated WhatsApp messages. Options: Meta's WhatsApp Cloud API directly, or a
BSP (Gupshup / Twilio / 360dialog) that wraps it.

## Decision (recommended)

Start on **Meta WhatsApp Cloud API** directly:

- Lowest per-message cost, no BSP markup.
- Templates ("report_ready", "plan_expiry_alert") submitted for approval up front.
- `apps/notifications/services.py` exposes a single `send_whatsapp(to, template,
  params)` function; the HTTP client is the only provider-specific code, so
  swapping to a BSP later is a one-file change.
- Config via `WHATSAPP_API_URL` + `WHATSAPP_API_TOKEN` (already in `.env`).
- Delivery status + retries recorded on `Notification` rows (Story MER-2/MER-4).

Switch to a BSP only if we need shared team inboxes, richer analytics, or
multi-number routing.

## Consequences

- Need a Meta Business account + a verified WhatsApp number + template approval
  lead time (days) — start this before Phase 4.
- Opt-in: merchants are onboarded by the Ops team (RD 2.4), so consent is
  captured at contract signing; record it on the merchant profile.
