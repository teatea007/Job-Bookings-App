# My Booking 360 — AppDeploy version (not deployed yet)

A standalone version of the app for AppDeploy, with its own sign-in and database instead of Claude storage.

- `src/app.js`, `src/styles.css` — generated from `../index.html` by `tools/port.py`
- `backend/index.ts` — per-user jobs, clients and settings API, backup import, calendar link
- `backend/ics.ts` — calendar subscription feed (replaces the Google Calendar connector)
- `appdeploy.auth-login.json`, `public/manifest.json`, `tests/tests.json` — login screen, home-screen manifest, AppDeploy test plan

Gmail is replaced by the phone's share sheet or the mail app with the PDF attached.
Regenerate the frontend after changing `../index.html`: `python3 appdeploy/tools/port.py`.
