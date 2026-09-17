// Read-only smoke proof against a LOCAL production build, never a remote site.
// Start Next on 127.0.0.1:3099 with synthetic build configuration first.
const assert = require('node:assert/strict');

async function main() {
  const results = [];
  for (const path of ['/register', '/register/nested', '/checkout/pro', '/checkout/scale']) {
    const response = await fetch(`http://127.0.0.1:3099${path}`, {
      redirect: 'manual', signal: AbortSignal.timeout(10000),
    });
    assert.equal(response.status, 403, `BETA_RESTRICTION_FAILED:${path}`);
    assert.match(response.headers.get('cache-control') || '', /no-store/, 'BETA_CACHE_POLICY_FAILED');
    assert.match(await response.text(), /invitation uniquement/, 'BETA_REFUSAL_BODY_FAILED');
    results.push({ path, status: response.status });
  }
  const response = await fetch('http://127.0.0.1:3099/login?redirect=%2Fcheckout%2Fpro', {
    redirect: 'manual', signal: AbortSignal.timeout(10000),
  });
  assert.equal(response.status, 200, 'BETA_LOGIN_UNAVAILABLE');
  const html = await response.text();
  assert.match(html, /Connexion professionnelle/, 'BETA_PROFESSIONAL_LOGIN_MISSING');
  assert.match(html, /Accès réservé aux deux professionnels invités/, 'BETA_INVITATION_NOTICE_MISSING');
  assert.doesNotMatch(html, /href="\/register"|Administrateur|finaliser votre abonnement|passer à PRO/, 'BETA_LEGACY_ENTRY_LEAK');
  assert.match(html, /href="\/forgot-password"/, 'BETA_RECOVERY_LINK_MISSING');
  results.push({ path: '/login?redirect=/checkout/pro', status: response.status });
  console.log(JSON.stringify({ status: 'PASS', scope: 'LOCAL_BUILT_HTTP_SURFACE_ONLY',
    checks: results, authentication_proven: false, browser_proven: false, production_proven: false }));
}
main().catch(() => {
  // No raw body, token, environment, or server diagnostic in the failure output.
  console.error('LOCAL_BETA_HTTP_CHECK_FAILED');
  process.exitCode = 1;
});
