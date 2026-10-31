# My Booking 360

Job booking, quoting, invoicing and payment tracking for sound, lighting and AV engineers and techs, set up for South Africa (ZAR, 15% VAT, SARS tax invoices).

**Open the app:** <https://teatea007.github.io/Job-Bookings-App/>
On iPhone, open it in Safari, then **Share → Add to Home Screen**. It runs full screen like a normal app.

The first time, follow [SETUP-GOOGLE.md](SETUP-GOOGLE.md) to connect your Google account (about 15 minutes, once).

## Features

- **Bookings** with client, engineer/tech, dates, call/finish times, venue, on-site contact and PO
- **Statuses**: Blocked off, Heavy pencil, Confirmed, Completed, Not completed, Cancelled, colour-coded
- **Charges**: day rate (quantity follows the number of booking days automatically), overtime, travel per km, expenses, VAT
- **Quotes**: numbered quotes with a valid-until date; email, share or save as PDF; "Client accepted" confirms the booking
- **Invoices**: numbered SARS-style tax invoices; email via Gmail, share or save as PDF; reminders for overdue invoices
- **Payments**: full or part payments, balances and overdue flags
- **Google Calendar sync** with status colours
- **Dashboard**, calendar view, clash warnings, charts, top clients, CSV exports for VAT201 / provisional tax
- **Backup and restore** to a file

## How it works

It's a static web app (one `index.html`) served by GitHub Pages. There's no server.

| Piece | How |
| --- | --- |
| Sign-in | Google OAuth in the browser (redirect flow, so it works in iPhone home-screen apps) |
| Saving | A private JSON file in the hidden *app data* area of your Google Drive, plus a copy on the device for speed and offline use |
| Calendar | Google Calendar API, your primary calendar |
| Email | Gmail API: sends quotes, invoices and reminders with the PDF attached, or saves drafts |
| Offline | A service worker (`sw.js`) caches the app so it opens without a connection; changes sync to Drive when you're back online |

Your Google client ID goes in `config.js`. It's not a secret: Google only accepts it from the addresses registered for it.

## Project layout

```
index.html              the app (HTML, CSS and JS in one file)
config.js               Google client ID
manifest.webmanifest    home-screen app details
sw.js                   offline cache
icons/                  app icons
SETUP-GOOGLE.md         one-off Google Cloud setup
artifact/index.html     the original claude.ai Artifact version (uses Claude's storage and connectors)
tests/                  Playwright checks
docs/screenshots/       screenshots with sample data
dev/patches/            scripts that applied earlier feature changes
```

## Running the checks

Needs Node and Playwright with Chromium.

```
npm install
npm test
```

`tests/standalone.test.js` runs the whole app against a fake Google: sign-in, saving to Drive, reloading, calendar sync, sending a quote and renewing an expired sign-in.
