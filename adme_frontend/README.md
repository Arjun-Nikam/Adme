# AdMe Ops App (Expo — React Native + react-native-web)

Operations app for **web**, **iOS**, and **Android**. It opens directly at the
AdMe Ops login and contains admin, merchant, driver, and superadmin routes.
Customer routes live in the separate `../adme_customer` app. After login the
app reads `role` from the JWT and Expo Router sends the user to the matching
route group (Story CORE-1). See `../docs/architecture.md` §15 and
`../docs/adr/0001-react-native-frontend.md`.

## Local setup

```bash
cp .env.example .env
npm install
npx expo start           # press w = web, i = iOS sim, a = Android emulator
```

Web only, in Docker (matches the compose stack): `docker compose up frontend`
→ http://localhost:8081/

## Scripts

| command | what |
|---|---|
| `npm start` | Expo dev server (all targets) |
| `npm run web` | web dev server only |
| `npm run export:web` | static web build (`dist/`) — CI runs this |
| `npm run lint` | eslint (`eslint-config-expo`) |
| `npm run typecheck` | `tsc --noEmit` |

## Layout

| path | purpose |
|---|---|
| `app/_layout.tsx` | providers (Redux, RTK Query) + session bootstrap from stored token |
| `app/login.tsx` | single login, role redirect |
| `app/(merchant)/` `(admin)/` `(rickshaw)/` `(superadmin)/` | operations route groups, each guarded by role |
| `src/api/` | RTK Query slices — `baseApi` + one per Django app (`authApi`, `merchantApi`, …) |
| `src/store/` | `configureStore` + `auth` slice |
| `src/lib/` | `storage` (secure-store / localStorage), `roles` (JWT role decode + `roleHome`) |
| `src/components/` | shared RN UI (`Screen`, `Card`, `RoleGuard`) |
| `src/theme/` + `tailwind.config.js` | NativeWind tokens |

## Conventions

- A new feature ≈ one `app/(role)/<screen>.tsx` + one endpoint in the matching
  `src/api/*Api.ts` slice. Keep the **Django app ⇄ route group ⇄ api slice**
  names aligned.
- Charts: `victory-native`. Maps: per ADR 0005. QR scan: `expo-camera`.
- Env vars must be prefixed `EXPO_PUBLIC_` to reach the client.
- Tokens go through `src/lib/storage` — never touch `localStorage` /
  `SecureStore` directly in a screen.
