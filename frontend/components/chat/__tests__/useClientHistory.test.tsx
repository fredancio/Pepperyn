import { act, renderHook } from '@testing-library/react';
import { useClientHistory } from '../useClientHistory';
import { fetchAnalysesHistory } from '@/lib/api';
jest.mock('@/lib/api', () => ({ fetchAnalysesHistory: jest.fn() }));
const fetchHistory = fetchAnalysesHistory as jest.Mock;
const row = (id: string) => ({ id, fichier_nom: id, created_at: '2026-01-01' });
beforeEach(() => jest.resetAllMocks());

test('late client A response cannot replace client B history', async () => {
  let resolveA!: (v: unknown) => void;
  fetchHistory.mockImplementation((id: string) => id === 'a' ? new Promise(r => { resolveA = r; }) : Promise.resolve([row('B')]));
  const { result, rerender } = renderHook(({ id }) => useClientHistory(id), { initialProps: { id: 'a' } });
  let old!: Promise<void>;
  act(() => { old = result.current.refresh(); });
  rerender({ id: 'b' });
  await act(async () => { await result.current.refresh(); });
  await act(async () => { resolveA([row('A')]); await old; });
  expect(result.current.sessions.map(s => s.id)).toEqual(['B']);
  expect(result.current.error).toBe(false);
});

test('latest same-client request wins and error is not empty success', async () => {
  let rejectOld!: (e: Error) => void;
  fetchHistory.mockImplementationOnce(() => new Promise((_, reject) => { rejectOld = reject; }))
    .mockResolvedValueOnce([row('latest')]).mockRejectedValueOnce(new Error('private'));
  const { result } = renderHook(() => useClientHistory('a'));
  let old!: Promise<void>;
  act(() => { old = result.current.refresh(); });
  await act(async () => { await result.current.refresh(); });
  await act(async () => { rejectOld(new Error('old')); await old; });
  expect(result.current.sessions[0].id).toBe('latest');
  expect(result.current.error).toBe(false);
  await act(async () => { await result.current.refresh(); });
  expect(result.current.error).toBe(true);
  expect(result.current.sessions).toEqual([]);
});
