// Real PostgreSQL semantics in an isolated PGlite engine, NOT Supabase proof.
// node test_v36_privileges.mjs <absolute path to @electric-sql/pglite/dist/index.js>
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
process.on('uncaughtException', e => { console.error(JSON.stringify({status:'FAIL', message:e.message, code:e.code})); process.exit(1); });
const { PGlite } = await import(process.argv[2] ? pathToFileURL(process.argv[2]).href : '@electric-sql/pglite');
const sql = await readFile(new URL('../migrations/v36_confine_legacy_client_privileges.sql', import.meta.url), 'utf8');
const postflight = await readFile(new URL('../sandbox/v36_privilege_postflight.sql', import.meta.url), 'utf8');
const tables = ['sessions','analyses','evidence_ledger_entries','arc_analysis_links','decision_arcs','knowledge_model'];
const all = [...tables, 'profiles', 'companies'];
const userA = '00000000-0000-4000-8000-000000000001';
const userB = '00000000-0000-4000-8000-000000000002';
let passed = 0;
async function setup() {
  const db = new PGlite();
  await db.exec(`CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role BYPASSRLS;
    GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
    CREATE SCHEMA auth;
    CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS
      $$ SELECT nullif(current_setting('request.jwt.claim.sub', true),'')::uuid $$;
    GRANT USAGE ON SCHEMA auth TO PUBLIC;
    CREATE TABLE public.entities (id uuid);
    CREATE FUNCTION public.create_entity_with_engagement(uuid,uuid,text,text,text,text)
      RETURNS SETOF public.entities LANGUAGE sql SECURITY DEFINER AS $$ SELECT * FROM public.entities $$;`);
  for (const t of all) {
    await db.exec(`CREATE TABLE public.${t} (id uuid PRIMARY KEY, company_id uuid, admin_user_id uuid, payload text);
      GRANT ALL ON public.${t} TO anon, authenticated, service_role;
      INSERT INTO public.${t} VALUES ('${userA}','${userA}','${userA}','synthetic-A'),('${userB}','${userB}','${userB}','synthetic-B');`);
  }
  await db.exec(`ALTER TABLE profiles ENABLE ROW LEVEL SECURITY; ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
    CREATE POLICY profiles_own ON profiles FOR ALL USING (id = auth.uid());
    CREATE POLICY companies_admin_own ON companies FOR ALL USING (admin_user_id = auth.uid());`);
  return db;
}
async function denied(db, query) {
  await assert.rejects(db.exec(query), e => e.code === '42501');
}
async function scenario(name, fn) {
  const db = await setup();
  try { await fn(db); passed++; console.log(`PASS ${name}`); } finally { await db.close(); }
}
await scenario('migration executes; all six tables deny both client roles; service read/write retained', async db => {
  await db.exec(sql);
  for (const role of ['anon','authenticated']) {
    await db.exec(`SET ROLE ${role}`);
    for (const t of tables) {
      await denied(db, `SELECT * FROM ${t}`);
      await denied(db, `INSERT INTO ${t}(id) VALUES ('00000000-0000-4000-8000-000000000003')`);
      await denied(db, `UPDATE ${t} SET payload='forged' WHERE false`);
      await denied(db, `DELETE FROM ${t} WHERE false`);
    }
    await denied(db, `SELECT * FROM create_entity_with_engagement(NULL,NULL,NULL,NULL,NULL,NULL)`);
    await db.exec('RESET ROLE');
  }
  await db.exec('SET ROLE service_role');
  for (const t of all) {
    assert.equal((await db.query(`SELECT * FROM ${t}`)).rows.length, 2);
    await db.exec(`INSERT INTO ${t}(id) VALUES ('00000000-0000-4000-8000-000000000003');
      UPDATE ${t} SET payload='synthetic-service' WHERE id='00000000-0000-4000-8000-000000000003';
      DELETE FROM ${t} WHERE id='00000000-0000-4000-8000-000000000003'`);
  }
  await db.exec('SELECT * FROM create_entity_with_engagement(NULL,NULL,NULL,NULL,NULL,NULL); RESET ROLE');
});
await scenario('two synthetic identities read own profile/company only; no self-reassignment/plan mutation', async db => {
  await db.exec(sql);
  for (const id of [userA,userB]) {
    await db.exec(`SET ROLE authenticated; SET request.jwt.claim.sub='${id}'`);
    for (const t of ['profiles','companies']) {
      assert.deepEqual((await db.query(`SELECT id FROM ${t}`)).rows, [{id}]);
      await denied(db, `UPDATE ${t} SET company_id='${userB}' WHERE id='${id}'`);
      await denied(db, `INSERT INTO ${t}(id) VALUES ('00000000-0000-4000-8000-000000000003')`);
      await denied(db, `DELETE FROM ${t} WHERE id='${id}'`);
    }
    await db.exec('RESET ROLE');
  }
  await db.exec('SET ROLE anon');
  for (const t of ['profiles','companies']) await denied(db, `SELECT * FROM ${t}`);
});
await scenario('independent column grants removed; replay preserves protections', async db => {
  await db.exec('GRANT UPDATE(company_id), SELECT(payload) ON profiles TO anon; GRANT SELECT(payload) ON analyses TO PUBLIC');
  await db.exec(sql); await db.exec(sql);
  await db.exec('SET ROLE anon');
  await denied(db, 'SELECT payload FROM analyses');
  await denied(db, 'UPDATE profiles SET company_id=NULL WHERE false');
});
await scenario('postflight detects baseline failure then bounded success; contents unchanged', async db => {
  const inspect = async () => (await db.exec(postflight)).flatMap(r => r.rows ?? []).find(r => r.v36_postflight)?.v36_postflight;
  const before = await inspect();
  assert.equal(before.table_checks_pass, false);
  assert.equal(before.rpc_checks_pass, false);
  const snapshot = await Promise.all(all.map(t => db.query(`SELECT * FROM ${t} ORDER BY id`)));
  await db.exec(sql);
  const after = await inspect();
  assert.equal(after.table_checks_pass, true);
  assert.equal(after.rpc_checks_pass, true);
  assert.equal(after.two_user_adversarial_proof, false);
  assert.equal(after.production_proof, false);
  assert.deepEqual(await Promise.all(all.map(t => db.query(`SELECT * FROM ${t} ORDER BY id`))), snapshot);
});
for (const [name, drift, expected] of [
  ['missing table', 'DROP TABLE sessions', 'V36_TABLE_SCHEMA_REFUSED'],
  ['unexpected backend policy', 'CREATE POLICY unexpected ON analyses USING (true)', 'V36_UNREVIEWED_POLICY_REFUSED'],
  ['identity policy drift', 'ALTER POLICY profiles_own ON profiles USING (true)', 'V36_IDENTITY_POLICY_DRIFT_REFUSED'],
  ['inherited grant', 'CREATE ROLE extra_reader; GRANT SELECT ON analyses TO extra_reader; GRANT extra_reader TO anon', 'V36_EFFECTIVE_TABLE_GRANT_REMAINS'],
  ['service access absent', 'REVOKE UPDATE ON profiles FROM service_role', 'V36_SERVICE_PRIVILEGE_REFUSED'],
]) await scenario(`${name} refuses and rolls back`, async db => {
  await db.exec(drift);
  await assert.rejects(db.exec(sql), e => e.message.includes(expected));
  await db.exec('ROLLBACK');
  assert.equal((await db.query("SELECT relrowsecurity FROM pg_class WHERE oid='analyses'::regclass")).rows[0].relrowsecurity, false);
  assert.equal((await db.query("SELECT has_table_privilege('anon','analyses','SELECT') AS allowed")).rows[0].allowed, true);
});
console.log(JSON.stringify({status:'PASS', scenarios:passed, engine:'PGlite 0.3.14', synthetic_only:true, supabase_used:false, deployed_isolation_proven:false}));
