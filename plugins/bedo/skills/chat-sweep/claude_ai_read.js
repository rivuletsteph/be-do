// The chat sweep's read of claude.ai (27 Nov 2026): her plain chats, her cloud Code
// sessions and her Cowork tasks, every open one, as one list for
// `run_checks.sh chats --sessions claude_ai.json`.
//
// Run it with the browser's javascript tool on a claude.ai tab where she is signed
// in, only with her yes that turn. Paste this file's text as it is; save the result
// as it comes (one JSON value) to claude_ai.json. Read only: nothing is changed.
//
// What it reads (the shapes were seen on 27 Nov 2026):
//   GET /api/organizations                                  → her org's uuid
//   GET /api/organizations/{ORG}/chat_conversations?limit=… → uuid, name, is_starred, is_archived, is_temporary
//   GET /v1/code/sessions?limit=200[&cursor=…]              → id, title, status, status_bucket, tags, trigger_id
//   GET /v1/code/sessions?tags=cowork-remote&limit=200      → the Cowork tasks
// Both /v1/code calls need `anthropic-version: 2023-06-01` or they 400. Scheduled
// runs (trigger_id) and anything archived are left out; the sweep never touches them.
await (async () => {
  const H = { 'anthropic-version': '2023-06-01' };
  const get = async (u, h) => {
    const r = await fetch(u, { headers: h || {} });
    if (!r.ok) throw new Error(`${r.status} on ${u.split('?')[0]}`);
    return r.json();
  };
  const orgs = await get('/api/organizations');
  const org = (orgs.find(o => (o.capabilities || []).includes('chat')) || orgs[0]).uuid;

  // plain chats: newest first; read on while a page comes back full and new
  const chats = [], seen = new Set();
  for (let off = 0, n = 0; n < 10; n++, off += 400) {
    const page = await get(`/api/organizations/${org}/chat_conversations?limit=400&offset=${off}`);
    const fresh = (page || []).filter(c => !seen.has(c.uuid));
    fresh.forEach(c => seen.add(c.uuid));
    chats.push(...fresh);
    if (!page || page.length < 400 || !fresh.length) break;
  }

  // cloud Code sessions, then the Cowork tasks, every page
  const code = [], ids = new Set();
  for (const base of ['/v1/code/sessions?limit=200', '/v1/code/sessions?tags=cowork-remote&limit=200']) {
    let cur = null, n = 0, more = true;
    while (more && n < 20) {
      const page = await get(base + (cur ? `&cursor=${encodeURIComponent(cur)}` : ''), H);
      (page.data || []).forEach(s => { if (!ids.has(s.id)) { ids.add(s.id); code.push(s); } });
      cur = page.next_cursor; more = !!cur; n++;
    }
    if (more) throw new Error(`more than ${n} pages of ${base}: stopped rather than give half a list`);
  }

  const data = [
    ...chats.filter(c => !c.is_archived && !c.is_temporary).map(c => ({
      surface: 'chat', uuid: c.uuid, name: c.name, is_starred: !!c.is_starred,
      created_at: c.created_at, updated_at: c.updated_at,
      project: c.project ? c.project.name : null,
    })),
    ...code.filter(s => s.status !== 'archived' && !s.trigger_id).map(s => ({
      surface: 'cloud', id: s.id, title: s.title, status: s.status, status_bucket: s.status_bucket,
      created_at: s.created_at, updated_at: s.updated_at, last_event_at: s.last_event_at,
      tags: (s.tags || []).filter(t => !t.startsWith('config:')),
      parent_session_id: (s.relations || {}).parent_session_id || null,
    })),
  ];
  return JSON.stringify({ claude_ai: {
    read: ['chat', 'cloud'], read_at: new Date().toISOString(),
    counts: { chats: chats.length, code: code.length, open: data.length }, data } });
})()
