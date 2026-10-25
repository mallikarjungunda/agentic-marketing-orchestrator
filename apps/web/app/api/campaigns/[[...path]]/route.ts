import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';
type Context = { params: Promise<{ path?: string[] }> };
async function proxy(request: NextRequest, context: Context) {
  const { path = [] } = await context.params;
  const valid = path.length === 0 || (path.length === 1 && /^[a-f0-9-]{36}$/.test(path[0])) || (path.length === 2 && /^[a-f0-9-]{36}$/.test(path[0]) && ['run', 'decision', 'launch'].includes(path[1]));
  if (!valid) return NextResponse.json({ detail: 'Unknown route' }, { status: 404 });
  // Same-origin POSTs only. This is a localhost demo, not end-user authentication.
  const origin = request.headers.get('origin');
  if (request.method === 'POST' && origin && origin !== request.nextUrl.origin) {
    return NextResponse.json({ detail: 'Invalid origin' }, { status: 403 });
  }
  try {
    const upstream = await fetch(`${process.env.API_BASE_URL || 'http://127.0.0.1:8000'}/campaigns${path.length ? '/' + path.join('/') : ''}`, {
      method: request.method,
      headers: { 'Content-Type': 'application/json', 'X-API-Key': process.env.API_KEY || '' },
      body: request.method === 'POST' ? await request.text() : undefined,
      cache: 'no-store',
      signal: AbortSignal.timeout(300000),
    });
    return new NextResponse(await upstream.text(), { status: upstream.status, headers: { 'Content-Type': 'application/json' } });
  } catch {
    return NextResponse.json({ detail: 'API unavailable. Check that the backend is running. If a request timed out, refresh before retrying.' }, { status: 502 });
  }
}
export { proxy as GET, proxy as POST };
