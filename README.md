# My Booking 360

Job booking, quoting, invoicing and payment tracking for sound, lighting and AV engineers and techs, set up for South Africa (ZAR, 15% VAT, SARS tax invoices).

The whole app is one file: [`index.html`](index.html). It runs as a Claude Artifact at
https://claude.ai/artifact/3HB5ZtUvgx1CvgBE17zb34 (private to the owner's Claude account) and can be added to an iPhone home screen from Safari (Share → Add to Home Screen).

## Features

- **Bookings** with client, engineer/tech, dates, call/finish times, venue, on-site contact and PO
- **Statuses**: Blocked off, Heavy pencil, Confirmed, Completed, Not completed, Cancelled, colour-coded
- **Charges**: day rate (quantity follows the number of booking days automatically), overtime, travel per km, expenses, VAT
- **Quotes**: numbered quotes with a valid-until date; email, share or save as PDF; "Client accepted" confirms the booking
- **Invoices**: numbered SARS-style tax invoices; email via Gmail, share or save as PDF; reminders for overdue invoices
- **Payments**: full or part payments, balances and overdue flags
- **Google Calendar sync** with status colours
- **Dashboard**, calendar view, clash warnings, charts, top clients, CSV exports for VAT201 / provisional tax
- v2 design from UX Pilot: big screen titles, cream and teal palette, status-coloured cards, booking carousel, one-tap WhatsApp / call / email for clients

## How it runs

When opened as a Claude Artifact the page uses the artifact runtime (`window.claude.use`) for:

| Capability | Used for |
| --- | --- |
| `db` | Saving jobs, clients and settings to the owner's Claude account |
| `mcp` | Google Calendar (`create_event`, `update_event`, `delete_event`) and Gmail (`send_message`, `create_draft`) |
| `downloads` | Saving PDFs and CSV exports |
| `user` | Checking the viewer is the owner |

Opened anywhere else (for example straight from disk), it falls back to saving in the browser's `localStorage`, and calendar/email are switched off.

## Project layout

```
index.html            the app (HTML, CSS and JS in one file)
tests/                Playwright checks used while building features
docs/screenshots/     current screens (v2 design) with sample data
docs/design/ux-pilot/ the UX Pilot designs the v2 look is based on
archive/v1-tropical/  the previous design, saved as a complete working copy (git tag ui-v1-tropical)
dev/patches/          the scripts that applied each feature change to index.html
```

## Running the checks

Needs Node and Playwright with Chromium.

```
npm install        # installs jsPDF, used by the PDF test
npm test
```

`tests/screenshots.js` writes screenshots: `node tests/screenshots.js "$PWD/index.html" docs/screenshots`.
