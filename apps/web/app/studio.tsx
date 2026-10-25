"use client";
import { FormEvent, useCallback, useEffect, useState } from 'react';
type Campaign = { id: string; title: string; audience: string; objective: string; status: string; version: number; events: { action: string; at: string; version: number }[]; result: { error?: string; plan?: { steps: string[] }; draft?: { subject: string; body: string }; review?: { passed: boolean; findings: string[] }; attempts?: number } };
async function request<T>(path = '', body?: object): Promise<T> {
  const response = await fetch('/api/campaigns' + path, { method: body === undefined ? 'GET' : 'POST', headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  const result = await response.json();
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Request failed. Check the form values.');
  return result;
}
export default function CampaignStudio({ mode }: { mode: string }) {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selected, setSelected] = useState<Campaign | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const load = useCallback(async () => {
    const all = await request<Campaign[]>(); setCampaigns(all); return all;
  }, []);
  useEffect(() => { load().catch(e => setError(e.message)); }, [load]);
  async function perform(work: () => Promise<void>) {
    setBusy(true); setError(''); setNotice('');
    try { await work(); } catch (e) { setError(e instanceof Error ? e.message : 'Something went wrong'); } finally { setBusy(false); }
  }
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget);
    await perform(async () => { setSelected(await request<Campaign>('', { title: data.get('title'), audience: data.get('audience'), objective: data.get('objective') })); await load(); });
  }
  async function action(name: string, body: object = {}) {
    if (!selected) return;
    await perform(async () => {
      const result = await request<{ receipt?: string }>(`/${selected.id}/${name}`, body);
      const all = await load(); setSelected(all.find(c => c.id === selected.id) || null);
      if (result.receipt) setNotice('Simulated launch recorded: ' + result.receipt);
    });
  }
  return <main>
    <header><div><p className="eyebrow">CAMPAIGN WORKSPACE</p><h1>From brief to approved campaign.</h1><p>Plan, create and review with a coordinated workflow.</p></div><span className="badge">{mode === 'demo' ? 'Demo · no model calls' : 'Live model'} · simulated launch</span></header>
    <div role="status" aria-live="polite">{busy && <p className="notice">Working… model workflows may take a few minutes.</p>}{notice && <p className="notice">{notice}</p>}</div>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="workspace"><aside>
      <section><h2>New campaign</h2><form onSubmit={create}>
        <label>Campaign name<input name="title" required minLength={3} maxLength={120} defaultValue="Business card introduction" /></label>
        <label>Audience<input name="audience" required minLength={3} maxLength={300} defaultValue="Small-business owners" /></label>
        <label>Objective<textarea name="objective" required minLength={10} maxLength={2000} defaultValue="Introduce expense tracking and monthly reporting." /></label>
        <button disabled={busy}>Create campaign</button>
      </form></section>
      <section><div className="section-title"><h2>Campaigns</h2><button className="secondary" disabled={busy} onClick={() => perform(async () => { const all = await load(); setSelected(all.find(c => c.id === selected?.id) || all[0] || null); })}>Refresh</button></div>
        {campaigns.length === 0 && <p>Your campaigns will appear here.</p>}
        {campaigns.map(c => <button className={'campaign ' + (selected?.id === c.id ? 'active' : '')} key={c.id} disabled={busy} onClick={() => { setSelected(c); setNotice(''); }}><strong>{c.title}</strong><span>{c.status.replaceAll('_', ' ')} · v{c.version}</span></button>)}
      </section>
    </aside><article>{!selected ? <section className="empty"><p className="eyebrow">YOUR NEXT CAMPAIGN STARTS HERE</p><h2>Give your agents a brief.</h2><p>Create a campaign to explore planning, content generation, review and human approval.</p><p>Uses fictional product information for demonstration.</p></section> : <>
      <section><div className="section-title"><h2>{selected.title}</h2><span className="badge">{selected.status.replaceAll('_', ' ')}</span></div><p>{selected.objective}</p><p>Audience: {selected.audience} · Draft version: {selected.version}</p>
      <div className="actions">
        {!['approved', 'launched'].includes(selected.status) && <button disabled={busy} onClick={() => action('run')}>{selected.version ? 'Generate new draft' : 'Run workflow'}</button>}
        {selected.status === 'awaiting_approval' && <><button disabled={busy} onClick={() => action('decision', { version: selected.version, decision: 'approve' })}>Approve v{selected.version}</button><button className="secondary" disabled={busy} onClick={() => action('decision', { version: selected.version, decision: 'reject' })}>Reject draft</button></>}
        {selected.status === 'approved' && <button disabled={busy} onClick={() => action('launch')}>Simulate launch</button>}
      </div>{selected.result.error && <p className="error">{selected.result.error}</p>}</section>
      {selected.result.plan && <section><h2>Campaign plan</h2><ol>{selected.result.plan.steps.map((step, i) => <li key={i}>{step}</li>)}</ol></section>}
      {selected.result.draft && <section><p className="eyebrow">EMAIL DRAFT · VERSION {selected.version}</p><h2>{selected.result.draft.subject}</h2><p className="draft">{selected.result.draft.body}</p></section>}
      {selected.result.review && <section><h2>Draft review</h2><p>{selected.result.review.passed ? 'Passed automated draft checks. Human approval is still required.' : 'Needs attention before approval.'}</p><p>{selected.result.attempts} generation attempt(s)</p><ul>{selected.result.review.findings.map((finding, i) => <li key={i}>{finding}</li>)}</ul></section>}
      <section><h2>Execution history</h2><ul className="history">{selected.events.map((event, i) => <li key={i}><strong>{event.action.replaceAll('_', ' ')}</strong><span>v{event.version} · {new Date(event.at).toLocaleString()}</span></li>)}</ul></section>
    </>}</article></div>
    <footer>Learning project · fictional product facts · automated review does not establish regulatory compliance.</footer>
  </main>;
}
