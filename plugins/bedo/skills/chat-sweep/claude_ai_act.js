// The chat sweep's own steps on claude.ai (27 Nov 2026): rename, unpin and archive
// the claude.ai chats and cloud sessions the sweep named, each read back.
//
// Run `run_checks.sh chats … --json`, then paste this file's text into the browser's
// javascript tool on a claude.ai tab with FOUND replaced by that JSON (the whole
// list, as it came). Run it again with START set to the `next` it returns until
// `next` is null: it does at most 25 a call, about 600 ms apart (twenty calls back
// to back return 429, and a long loop hits the tool's time limit).
//
// For each chat in FOUND whose surface is `chat` or `cloud`, and never one marked busy
// or routine:
//   rename  → its `rename` title, first (her rule: the status glyph before the archive)
//   unpin   → claude.ai chat: is_starred false · cloud: the ui:pinned tag removed
//   archive → only when its verdict is `archive`; a close_row, carry or entry is
//             archived after its row is written, by running the sweep again
// Calls: PUT /api/organizations/{ORG}/chat_conversations/{uuid} {name | is_starred |
// is_archived}; PUT /v1/code/sessions/{id} {title | tags}; POST
// /v1/code/sessions/{id}/archive {}. Tried 27 Nov 2026: the cloud archive (200, read
// back archived) and the unstar (202). The chat archive and the tag removal were
// not yet tried: the read-back says whether they took. A failure is reported, never
// retried blind.
await (async () => {
  const FOUND = __FOUND__;   // ← the sweep's --json output
  const START = 0;           // ← the `next` from the last run
  const H = { 'anthropic-version': '2023-06-01', 'content-type': 'application/json' };
  const J = { 'content-type': 'application/json' };
  const pause = () => new Promise(r => setTimeout(r, 600));
  const orgs = await fetch('/api/organizations').then(r => r.json());
  const org = (orgs.find(o => (o.capabilities || []).includes('chat')) || orgs[0]).uuid;
  const chatUrl = id => `/api/organizations/${org}/chat_conversations/${id}`;
  const codeUrl = id => `/v1/code/sessions/${id}`;

  const steps = [];
  for (const x of FOUND) {
    if (!['chat', 'cloud'].includes(x.surface) || ['busy', 'routine'].includes(x.verdict)) continue;
    if (x.rename) steps.push([x, 'rename']);
    if (x.unpin) steps.push([x, 'unpin']);
    if (x.verdict === 'archive') steps.push([x, 'archive']);
  }

  const done = [];
  const end = Math.min(steps.length, START + 25);
  for (let i = START; i < end; i++) {
    const [x, what] = steps[i];
    let status, ok;
    try {
      if (x.surface === 'chat') {
        const body = what === 'rename' ? { name: x.rename } : what === 'unpin' ? { is_starred: false } : { is_archived: true };
        status = (await fetch(chatUrl(x.id), { method: 'PUT', headers: J, body: JSON.stringify(body) })).status;
        await pause();
        const c = await fetch(chatUrl(x.id)).then(r => r.json());
        ok = what === 'rename' ? c.name === x.rename : what === 'unpin' ? !c.is_starred : !!c.is_archived;
      } else {
        if (what === 'archive') {
          status = (await fetch(codeUrl(x.id) + '/archive', { method: 'POST', headers: H, body: '{}' })).status;
        } else {
          let body = { title: x.rename };
          if (what === 'unpin') {
            const now = await fetch(codeUrl(x.id), { headers: H }).then(r => r.json());
            body = { tags: (now.tags || []).filter(t => t !== 'ui:pinned') };
          }
          status = (await fetch(codeUrl(x.id), { method: 'PUT', headers: H, body: JSON.stringify(body) })).status;
        }
        await pause();
        const s = await fetch(codeUrl(x.id), { headers: H }).then(r => r.json());
        ok = what === 'rename' ? s.title === x.rename
           : what === 'unpin' ? !(s.tags || []).includes('ui:pinned') : s.status === 'archived';
      }
    } catch (e) { status = String(e); ok = false; }
    done.push({ what, surface: x.surface, id: x.id, title: (x.rename || x.title).slice(0, 60), status, ok });
    await pause();
  }
  return JSON.stringify({ steps: steps.length, from: START, next: end < steps.length ? end : null,
                          failed: done.filter(d => !d.ok), done });
})()
