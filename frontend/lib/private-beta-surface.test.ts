/** @jest-environment node */
import { NextRequest } from 'next/server';
import { middleware, config } from '../middleware';

afterEach(() => jest.restoreAllMocks());

test.each([
  ['production', '0', 403], ['development', '1', 403],
  ['development', 'invalid', 403], ['development', '0', 200],
] as const)('public signup restriction %s/%s', async (nodeEnv, flag, status) => {
  jest.replaceProperty(process, 'env', { ...process.env, NODE_ENV: nodeEnv, PEPPERYN_PRIVATE_BETA: flag });
  const response = middleware(new NextRequest('http://local/register'));
  expect(response.status).toBe(status);
  if (status === 403) {
    expect(response.headers.get('cache-control')).toBe('no-store');
    expect(await response.text()).toContain('invitation');
  }
});

test('matcher covers register and checkout without blocking login or auth callback', () => {
  expect(config.matcher).toEqual(['/register/:path*', '/checkout/:path*']);
});
