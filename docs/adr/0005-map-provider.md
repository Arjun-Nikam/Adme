# ADR 0005 — Map provider for the live fleet map

- **Status:** Proposed (needs a commercial call before Phase 6)
- **Date:** 2026-08-30

## Context

Story RIK-2: an interactive map plotting the latest GPS ping per active rickshaw,
auto-refreshing every 10–15 s, marker click → registration / driver / hardware.
Also used for area-mapping decisions (RD 2.10). The frontend is now React Native
(Expo), so the SDK choice is coupled to RN support.

## Options

| | `react-native-maps` | `@rnmapbox/maps` |
|---|---|---|
| Native perf w/ 100s of markers | good (Google/Apple native) | very good (vector, GL) |
| Web (`react-native-web`) | needs a shim (`react-native-web-maps`) or a separate `@vis.gl/react-google-maps` web path | official web support (Mapbox GL JS) |
| Pricing | Google Maps Platform (map loads + geocoding) | Mapbox (MAU-based) |
| Offline / custom styling | limited | strong |
| Setup in Expo | config plugin, needs a dev build | config plugin, needs a dev build |

## Recommendation

**`@rnmapbox/maps`** — consistent web + native rendering (one code path for the
fleet map on the web Ops Screen and the mobile app), better with many live
markers, MAU pricing is predictable for an internal tool. Requires a Mapbox
account + access token (`EXPO_PUBLIC_MAPS_API_KEY`).

Fall back to `react-native-maps` + Google if the team already has Google Maps
Platform billing and wants Google tiles/Street View.

Decide before Phase 6; nothing earlier depends on it.
