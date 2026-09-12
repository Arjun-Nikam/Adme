# ADR 0001 — React Native (Expo) for the frontend

- **Status:** Accepted
- **Date:** 2026-08-30
- **Supersedes:** the "Frontend: React JS (Vite)" decision in
  `Adme_OpsScreen_Dev_Plan.docx` §3 / §6.2

## Context

The `.docx` specified a React + Vite web SPA. The business needs the Ops Screen
reachable as a **web app** (merchant / admin / super_admin) **and** as **iOS +
Android apps** (consumer scanning offers, driver KYC/telemetry, hardware device
screen). The consumer flow in particular (camera QR scan, live GPS "near me",
push) is mobile-first and awkward as a pure web app.

Maintaining a separate web SPA and native app doubles the surface area and
guarantees drift.

## Decision

Build the frontend as a **single React Native codebase on Expo**, using
`react-native-web` for the web target.

- **Expo (managed) + Expo Router** — file-based routing, one route group per RD
  role; EAS Build for store/internal binaries; OTA updates; first-class
  `expo-camera`, `expo-location`, `expo-secure-store`, `expo-notifications`.
- **RTK Query** for the API layer (replaces hand-written `xApi.js` modules),
  Redux Toolkit for the little client state (auth).
- **victory-native** for charts (Recharts is DOM-only), **NativeWind** for
  styling, **react-hook-form** for forms.
- Web is shipped as a static export (`expo export -p web`) behind Nginx/CDN;
  native via EAS Build.

The existing `adme_frontend/` React+Vite scaffold (routing/store/guard skeleton,
stub screens, no business logic) is **replaced in place**.

## Consequences

- One codebase, one set of screens, one API layer for all three targets.
- Native capabilities (camera, GPS, push, deep links) available without a second
  project.
- Cost: Metro/Expo build toolchain instead of Vite; charts and maps use RN
  libraries; contributors need a simulator/emulator for native work (web still
  runs in a browser).
- `.docx` §3 stack table and §6.2 folder structure are superseded by
  `architecture.md` §15.
- CI changes: `npm run build` → `expo export -p web` + `eslint` + `tsc`.
- Driver + hardware builds are distributed internally (EAS internal
  distribution / MDM), not via public app stores.

## Alternatives considered

- **Bare React Native CLI + react-native-web** — more control over native
  modules, materially more setup/maintenance; rejected for an intern-heavy team.
- **Keep React web + add a separate RN app** — two codebases, drift; rejected.
- **PWA only** — no real camera/push story on iOS, fails the consumer use case.
