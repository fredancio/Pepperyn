import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import LoginScreen from './LoginScreen';
import LoginPage from '@/app/login/page';
import { signInAdmin } from '@/lib/auth';

const replace = jest.fn();
let redirect: string | null = null;
jest.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
  useSearchParams: () => ({ get: () => redirect }),
}));
jest.mock('@/lib/auth', () => ({ signInAdmin: jest.fn() }));
jest.mock('./PinLoginForm', () => ({ PinLoginForm: () => <div>Legacy PIN form</div> }));

beforeEach(() => { jest.clearAllMocks(); redirect = null; });
afterEach(() => jest.restoreAllMocks());

test('Beta offers professional password access, not admin role, PIN, signup or purchase', () => {
  render(<LoginScreen privateBeta />);
  expect(screen.getByRole('heading', { name: /Connexion professionnelle/ })).toBeInTheDocument();
  expect(screen.queryByText(/Administrateur/)).not.toBeInTheDocument();
  expect(screen.queryByText(/Invité/)).not.toBeInTheDocument();
  expect(screen.queryByText('Legacy PIN form')).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: 'Créer mon espace' })).not.toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Mot de passe oublié ?' })).toHaveAttribute('href', '/forgot-password');
});

test.each([
  ['/app/portfolio', '/app/portfolio'], ['/checkout/pro', '/app/chat'],
  ['https://foreign.invalid', '/app/chat'], ['/app/../checkout/pro', '/app/chat'],
])('Beta login redirect %s stays in the professional workspace', async (requested, expected) => {
  redirect = requested;
  (signInAdmin as jest.Mock).mockResolvedValue({});
  render(<LoginScreen privateBeta />);
  fireEvent.change(screen.getByLabelText('Adresse email'), { target: { value: 'synthetic@example.invalid' } });
  fireEvent.change(screen.getByPlaceholderText('Votre mot de passe'), { target: { value: 'synthetic-test-only' } });
  fireEvent.click(screen.getByRole('button', { name: 'Se connecter →' }));
  await waitFor(() => expect(replace).toHaveBeenCalledWith(expected));
  expect(signInAdmin).toHaveBeenCalledTimes(1);
});

test('ordinary non-Beta development retains the existing guest and signup surface', () => {
  render(<LoginScreen privateBeta={false} />);
  expect(screen.getByRole('link', { name: 'Créer mon espace' })).toHaveAttribute('href', '/register');
  fireEvent.click(screen.getByRole('button', { name: /Invité/ }));
  expect(screen.getByText('Legacy PIN form')).toBeInTheDocument();
});

test.each(['production', 'development'] as const)('server page uses the shared Beta policy: %s', env => {
  jest.replaceProperty(process, 'env', { ...process.env, NODE_ENV: env, PEPPERYN_PRIVATE_BETA: '1' });
  expect(LoginPage().props.privateBeta).toBe(true);
});
