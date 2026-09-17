// Call only from server entrypoints. This policy is surface UX, not authorization.
export function isPrivateBetaSurface(): boolean {
  return process.env.NODE_ENV === 'production' ||
    (process.env.PEPPERYN_PRIVATE_BETA ?? '0') !== '0';
}
