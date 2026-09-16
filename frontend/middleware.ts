import { NextRequest, NextResponse } from 'next/server';

// Surface restriction only. Supabase public signup must also be disabled in
// the actual project; backend verified-user admission remains authoritative.
export function middleware(request: NextRequest) {
  const beta = process.env.NODE_ENV === 'production' ||
    (process.env.PEPPERYN_PRIVATE_BETA ?? '0') !== '0';
  if (beta) {
    return new NextResponse('Private Beta sur invitation uniquement. Inscription publique et achat indisponibles.', {
      status: 403,
      headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' },
    });
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/register/:path*', '/checkout/:path*'],
};
