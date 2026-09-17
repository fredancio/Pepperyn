import LoginScreen from '@/components/auth/LoginScreen';
import { isPrivateBetaSurface } from '@/lib/private-beta-policy';

// Resolve server-only configuration per request; never expose tester IDs.
export const dynamic = 'force-dynamic';

export default function LoginPage() {
  return <LoginScreen privateBeta={isPrivateBetaSurface()} />;
}
