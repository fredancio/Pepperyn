jest.mock('./supabase', () => ({ supabase: { auth: { getSession: async () => ({ data: { session: null } }) } } }));

beforeEach(() => { jest.resetModules(); process.env.NEXT_PUBLIC_GOVERNED_PIPELINE_TRANSPORT = '1'; sessionStorage.clear(); });
afterEach(() => { delete process.env.NEXT_PUBLIC_GOVERNED_PIPELINE_TRANSPORT; });

test('one upload then authoritative read, with no parallel legacy write', async () => {
  const api = await import('./api');
  global.fetch = jest.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'PERSISTED', analysis_id: 'owned' }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ analysis_id: 'owned', result: {}, execution_provenance: { status: 'VERIFIED_RECEIPT', receipt: {} } }) });
  const result = await api.analyzeV1SyntheticWorkbook(new File(['synthetic'], 'synthetic.xlsx'), 'entity');
  expect(result.analyse_id).toBe('owned');
  expect(result.result._execution_provenance.status).toBe('VERIFIED_RECEIPT');
  expect(global.fetch).toHaveBeenCalledTimes(2);
  expect(global.fetch).toHaveBeenNthCalledWith(1,expect.stringContaining('/api/governed/analyses'),expect.objectContaining({method:'POST'}));
  expect(global.fetch).toHaveBeenNthCalledWith(2,expect.stringContaining('/api/governed/analyses/owned'),expect.not.objectContaining({method:'POST'}));
});

test('uncertain upload never retries or falls back', async () => {
  const api = await import('./api');
  global.fetch = jest.fn().mockRejectedValue(new Error('offline'));
  await expect(api.analyzeV1SyntheticWorkbook(new File(['x'],'synthetic.xlsx'),'entity')).rejects.toThrow('Ne relancez pas');
  expect(global.fetch).toHaveBeenCalledTimes(1);
});

test('persisted but unreadable result retains its id and never repeats POST', async () => {
  const api = await import('./api');
  global.fetch = jest.fn().mockResolvedValueOnce({ok:true,json:async()=>({status:'PERSISTED',analysis_id:'owned'})})
    .mockResolvedValueOnce({ok:false,json:async()=>({})});
  await expect(api.analyzeV1SyntheticWorkbook(new File(['x'],'synthetic.xlsx'),'entity')).rejects.toThrow('Analyse enregistrée (owned)');
  expect(global.fetch).toHaveBeenCalledTimes(2);
});

test('export uses same owned boundary', async () => {
  const api=await import('./api');
  global.fetch=jest.fn().mockResolvedValue({ok:true,blob:async()=>new Blob(['test'])});
  await api.downloadV1GovernedExport('owned','pdf');
  expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/governed/analyses/owned/export.pdf'),expect.anything());
});

test('history read carries the authoritative temporal snapshot without another request', async () => {
  const api = await import('./api');
  const temporal = { current_analysis_id: 'owned', status: 'CONTRADICTION' };
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({
    analysis_id: 'owned', result: {}, execution_provenance: { status: 'VERIFIED_RECEIPT' }, temporal_comparison: temporal,
  }) });
  const data = await api.fetchV1GovernedAnalysis('owned');
  expect(data.result._governed_temporal_snapshot).toEqual(temporal);
  expect(global.fetch).toHaveBeenCalledTimes(1);
});
