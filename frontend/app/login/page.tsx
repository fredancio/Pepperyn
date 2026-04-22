import { redirect } from 'next/navigation';

/**
 * L'accès invité par PIN est conservé en backend pour usage futur (versions payantes).
 * En v3 MVP, la page /login est redirigée vers /register (seule porte d'entrée).
 */
export default function LoginPage() {
  redirect('/register');
}
