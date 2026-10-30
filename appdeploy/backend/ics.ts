// Builds an iCalendar (.ics) feed from saved bookings.
// Kept in step with buildIcs() in src/app.js, which makes single-booking files on the device.

type Rec = Record<string, unknown>;

const LABELS: Record<string, string> = {
  blocked: 'Blocked off',
  heavy: 'Heavy pencil',
  confirmed: 'Confirmed',
  completed: 'Completed',
  notdone: 'Not completed',
  cancelled: 'Cancelled',
};

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const TIME_RE = /^\d{2}:\d{2}$/;
const TZ_RE = /^[A-Za-z_]+(\/[A-Za-z0-9_+-]+)+$/;

const str = (v: unknown): string => (v === null || v === undefined ? '' : String(v));

function text(v: string): string {
  return v.replace(/\\/g, '\\\\').replace(/\r?\n/g, '\\n').replace(/([,;])/g, '\\$1');
}

function fold(line: string): string {
  const enc = new TextEncoder();
  let out = '';
  let cur = '';
  let n = 0;
  for (const ch of line) {
    const b = enc.encode(ch).length;
    if (n + b > 74) {
      out += cur + '\r\n ';
      cur = '';
      n = 1;
    }
    cur += ch;
    n += b;
  }
  return out + cur;
}

function addDays(iso: string, days: number): string {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d + days)).toISOString().slice(0, 10);
}

function event(j: Rec, client: Rec | undefined, tz: string, stamp: string): string[] {
  const start = str(j.start);
  if (!DATE_RE.test(start)) return [];
  const endRaw = str(j.end);
  const end = DATE_RE.test(endRaw) && endRaw > start ? endRaw : start;
  const status = str(j.status) || 'heavy';
  const label = LABELS[status] || status;
  const call = TIME_RE.test(str(j.callTime)) ? str(j.callTime) : '';
  const lines = ['BEGIN:VEVENT', `UID:${str(j.id)}@mybooking360`, `DTSTAMP:${stamp}`];

  if (call) {
    let fin = TIME_RE.test(str(j.finishTime)) ? str(j.finishTime) : '';
    if (!fin) {
      const [h, m] = call.split(':').map(Number);
      fin = `${String(Math.min(23, h + 1)).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
    }
    let endDay = end;
    if (endDay === start && fin <= call) endDay = addDays(endDay, 1);
    lines.push(
      `DTSTART;TZID=${tz}:${start.replace(/-/g, '')}T${call.replace(':', '')}00`,
      `DTEND;TZID=${tz}:${endDay.replace(/-/g, '')}T${fin.replace(':', '')}00`,
    );
  } else {
    lines.push(
      `DTSTART;VALUE=DATE:${start.replace(/-/g, '')}`,
      `DTEND;VALUE=DATE:${addDays(end, 1).replace(/-/g, '')}`,
    );
  }

  const engineer = str(j.engineer);
  const summary = (status === 'confirmed' ? '' : `[${label}] `) + (str(j.title) || 'Booking') + (engineer ? ` — ${engineer}` : '');
  const desc = [
    `Status: ${label}`,
    client && str(client.name) ? `Client: ${str(client.name)}` : '',
    engineer ? `Engineer / tech: ${engineer}${str(j.role) ? ` (${str(j.role)})` : ''}` : '',
    str(j.siteContact) ? `On-site: ${str(j.siteContact)} ${str(j.sitePhone)}`.trim() : '',
    str(j.po) ? `PO / ref: ${str(j.po)}` : '',
    str(j.notes) ? `\n${str(j.notes)}` : '',
    '\nManaged in My Booking 360',
  ].filter(Boolean).join('\n');
  const location = [str(j.venue), str(j.address)].filter(Boolean).join(', ');

  lines.push(`SUMMARY:${text(summary)}`, `DESCRIPTION:${text(desc)}`);
  if (location) lines.push(`LOCATION:${text(location)}`);
  lines.push(
    `STATUS:${status === 'cancelled' ? 'CANCELLED' : status === 'heavy' || status === 'blocked' ? 'TENTATIVE' : 'CONFIRMED'}`,
    `TRANSP:${status === 'cancelled' || status === 'notdone' ? 'TRANSPARENT' : 'OPAQUE'}`,
    'END:VEVENT',
  );
  return lines;
}

export function buildIcs(jobs: Rec[], clients: Map<string, Rec>, timeZone: string): string {
  const tz = TZ_RE.test(timeZone) ? timeZone : 'Africa/Johannesburg';
  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//My Booking 360//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'X-WR-CALNAME:My Booking 360',
    `X-WR-TIMEZONE:${tz}`,
    'REFRESH-INTERVAL;VALUE=DURATION:PT1H',
    'X-PUBLISHED-TTL:PT1H',
  ];
  for (const j of jobs) lines.push(...event(j, clients.get(str(j.clientId)), tz, stamp));
  lines.push('END:VCALENDAR');
  return lines.map(fold).join('\r\n') + '\r\n';
}
