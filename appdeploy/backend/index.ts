import { router, json, error, requireAuth, db, isAppDatabaseError } from '@appdeploy/sdk';
import type { RouterContext, RouterResponse, RouterRoutes } from '@appdeploy/sdk';
import { createHash, randomBytes } from 'crypto';
import { buildIcs } from './ics';

type Rec = Record<string, unknown>;
type Kind = 'jobs' | 'clients';

const MAX_RECORD_BYTES = 200000;
const MAX_IMPORT_BYTES = 900000;
const ID_RE = /^[A-Za-z0-9_-]{4,64}$/;
const TOKEN_RE = /^[a-f0-9]{36}$/;

// Table names may not contain arbitrary user IDs, so each user gets a hash-derived key.
function userKey(userId: string): string {
  return createHash('sha256').update(userId).digest('hex').slice(0, 32);
}

function tableFor(kind: Kind, key: string): string {
  return `${kind}_${key}`;
}

function keyOf(ctx: RouterContext): string {
  return userKey(ctx.user!.userId);
}

function asRecord(v: unknown): Rec | null {
  return v && typeof v === 'object' && !Array.isArray(v) ? (v as Rec) : null;
}

function bytes(v: unknown): number {
  return new TextEncoder().encode(JSON.stringify(v)).length;
}

function validRecord(kind: Kind, rec: Rec): string | null {
  if (typeof rec.id !== 'string' || !ID_RE.test(rec.id)) return 'Invalid record id';
  if (kind === 'jobs' && (typeof rec.title !== 'string' || !rec.title.trim())) return 'A booking needs an event name';
  if (kind === 'clients' && (typeof rec.name !== 'string' || !rec.name.trim())) return 'A client needs a name';
  if (bytes(rec) > MAX_RECORD_BYTES) return 'Record too large';
  return null;
}

function fail(e: unknown, what: string): RouterResponse {
  if (isAppDatabaseError(e)) {
    console.error(`${what} failed`, e.code, e.message);
    if (e.code === 'AppDatabaseQuotaExceeded') return error('Too many requests, try again shortly', 429);
    if (e.code === 'AppDatabaseItemTooLarge' || e.code === 'AppDatabaseRequestTooLarge') return error('Record too large', 413);
  } else {
    console.error(`${what} failed`, e);
  }
  return error('Server error', 500);
}

async function readSettings(key: string, consistent = false): Promise<Rec | null> {
  const [s] = await db.get<Rec>('settings', [key], { consistent });
  return s || null;
}

async function listAll(table: string, maxPages: number): Promise<Rec[]> {
  const out: Rec[] = [];
  let next: string | undefined;
  for (let i = 0; i < maxPages; i++) {
    const page = await db.list<Rec>(table, { limit: 100, nextToken: next });
    out.push(...page.items);
    next = page.nextToken;
    if (!next) break;
  }
  return out;
}

function crud(kind: Kind): RouterRoutes {
  return {
    [`GET /api/${kind}`]: [
      requireAuth(),
      async (ctx) => {
        try {
          const next = typeof ctx.query.next === 'string' && ctx.query.next ? ctx.query.next : undefined;
          const page = await db.list<Rec>(tableFor(kind, keyOf(ctx)), { limit: 100, nextToken: next });
          return json({ items: page.items, next: page.nextToken || null });
        } catch (e) {
          return fail(e, `list ${kind}`);
        }
      },
    ],
    [`PUT /api/${kind}/:id`]: [
      requireAuth(),
      async (ctx) => {
        const rec = asRecord(ctx.body);
        if (!rec || rec.id !== ctx.params.id) return error('Invalid record', 400);
        const problem = validRecord(kind, rec);
        if (problem) return error(problem, problem === 'Record too large' ? 413 : 400);
        try {
          const [ok] = await db.tx.update(tableFor(kind, keyOf(ctx)), [{ id: ctx.params.id, record: rec }]);
          if (!ok) return error('Not saved', 500);
          return json({ ok: true, id: ctx.params.id });
        } catch (e) {
          return fail(e, `save ${kind}`);
        }
      },
    ],
    [`DELETE /api/${kind}/:id`]: [
      requireAuth(),
      async (ctx) => {
        if (!ID_RE.test(ctx.params.id)) return error('Invalid record id', 400);
        try {
          await db.delete(tableFor(kind, keyOf(ctx)), [ctx.params.id]);
          return json({ ok: true });
        } catch (e) {
          return fail(e, `delete ${kind}`);
        }
      },
    ],
  };
}

export const handler = router({
  'GET /api/_healthcheck': [async () => json({ message: 'Success' })],

  ...crud('jobs'),
  ...crud('clients'),

  'GET /api/settings': [
    requireAuth(),
    async (ctx) => {
      try {
        return json({ settings: await readSettings(keyOf(ctx)) });
      } catch (e) {
        return fail(e, 'read settings');
      }
    },
  ],

  'PUT /api/settings': [
    requireAuth(),
    async (ctx) => {
      const rec = asRecord(ctx.body);
      if (!rec) return error('Invalid settings', 400);
      if (bytes(rec) > MAX_RECORD_BYTES) return error('Settings too large', 413);
      const key = keyOf(ctx);
      try {
        // The calendar token is only ever set by POST /api/cal-token.
        const current = await readSettings(key, true);
        const record: Rec = { ...rec };
        delete record.calToken;
        if (current && typeof current.calToken === 'string') record.calToken = current.calToken;
        const [ok] = await db.tx.update('settings', [{ id: key, record }]);
        if (!ok) return error('Not saved', 500);
        return json({ ok: true });
      } catch (e) {
        return fail(e, 'save settings');
      }
    },
  ],

  'POST /api/import': [
    requireAuth(),
    async (ctx) => {
      const body = asRecord(ctx.body);
      if (!body) return error('Invalid import', 400);
      if (bytes(body) > MAX_IMPORT_BYTES) return error('Import batch too large', 413);
      const key = keyOf(ctx);
      const counts: Record<Kind, number> = { jobs: 0, clients: 0 };
      try {
        for (const kind of ['clients', 'jobs'] as Kind[]) {
          const list = body[kind];
          if (list === undefined) continue;
          if (!Array.isArray(list) || list.length > 100) return error(`Send at most 100 ${kind} at a time`, 400);
          const items: { id: string; record: Rec }[] = [];
          for (const raw of list) {
            const rec = asRecord(raw);
            const problem = rec ? validRecord(kind, rec) : 'Invalid record';
            if (problem || !rec) return error(problem || 'Invalid record', 400);
            items.push({ id: rec.id as string, record: rec });
          }
          if (items.length) {
            await db.tx.update(tableFor(kind, key), items);
            counts[kind] = items.length;
          }
        }
        return json({ ok: true, imported: counts });
      } catch (e) {
        return fail(e, 'import');
      }
    },
  ],

  'POST /api/cal-token': [
    requireAuth(),
    async (ctx) => {
      const key = keyOf(ctx);
      try {
        const current = await readSettings(key, true);
        const token = randomBytes(18).toString('hex');
        await db.tx.add('caltokens', [{ id: token, owner: key }]);
        if (current && typeof current.calToken === 'string' && TOKEN_RE.test(current.calToken)) {
          await db.delete('caltokens', [current.calToken]);
        }
        const [ok] = await db.tx.update('settings', [{ id: key, record: { ...(current || {}), calToken: token } }]);
        if (!ok) return error('Not saved', 500);
        return json({ token });
      } catch (e) {
        return fail(e, 'create calendar link');
      }
    },
  ],

  // Public, unguessable calendar feed for subscribing from the phone's Calendar app.
  'GET /api/cal/:file': [
    async (ctx) => {
      const token = ctx.params.file.replace(/\.ics$/i, '');
      if (!TOKEN_RE.test(token)) return error('Not found', 404);
      try {
        const [link] = await db.get<Rec>('caltokens', [token]);
        const owner = link && typeof link.owner === 'string' ? link.owner : '';
        if (!owner) return error('Not found', 404);
        const [settings, jobs, clients] = await Promise.all([
          readSettings(owner),
          listAll(tableFor('jobs', owner), 10),
          listAll(tableFor('clients', owner), 5),
        ]);
        const byId = new Map<string, Rec>(clients.map((c) => [String(c.id), c]));
        const tz = settings && typeof settings.timeZone === 'string' ? settings.timeZone : 'Africa/Johannesburg';
        return {
          statusCode: 200,
          headers: {
            'Content-Type': 'text/calendar; charset=utf-8',
            'Content-Disposition': 'inline; filename="my-booking-360.ics"',
            'Cache-Control': 'private, max-age=900',
          },
          body: buildIcs(jobs, byId, tz),
        };
      } catch (e) {
        return fail(e, 'calendar feed');
      }
    },
  ],
});
