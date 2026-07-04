'use client';
import { useRef, useState, KeyboardEvent, ClipboardEvent } from 'react';
import { loginWithPinAndEmail } from '@/lib/api';
import { saveGuestAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export function PinLoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [digits, setDigits] = useState(['', '', '', '']);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [shake, setShake] = useState(false);

  const ref0 = useRef<HTMLInputElement>(null);
  const ref1 = useRef<HTMLInputElement>(null);
  const ref2 = useRef<HTMLInputElement>(null);
  const ref3 = useRef<HTMLInputElement>(null);
  const refs = [ref0, ref1, ref2, ref3];

  const triggerShake = () => {
    setShake(true);
    setTimeout(() => setShake(false), 600);
  };

  const handleDigitChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const char = value.slice(-1);
    const newDigits = [...digits];
    newDigits[index] = char;
    setDigits(newDigits);
    setError('');

    if (char && index < 3) {
      refs[index + 1].current?.focus();
    }
    if (char && index === 3) {
      const pin = [...newDigits.slice(0, 3), char].join('');
      if (pin.length === 4 && email.trim()) handleSubmit(pin);
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      refs[index - 1].current?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 4);
    if (pasted.length === 4) {
      setDigits(pasted.split(''));
      if (email.trim()) handleSubmit(pasted);
    }
  };

  const handleSubmit = async (pin?: string) => {
    const finalPin = pin || digits.join('');
    if (finalPin.length !== 4) { setError('Entrez les 4 chiffres du PIN'); return; }
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Entrez une adresse email valide');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const data = await loginWithPinAndEmail(email.trim(), finalPin);
      saveGuestAuth(data.access_token, data.company_id, data.plan);
      router.push('/app/chat');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Email ou code PIN incorrect');
      triggerShake();
      setDigits(['', '', '', '']);
      refs[0].current?.focus();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-[#5F6368] text-center">
        Connectez-vous avec votre email et le code PIN de votre entreprise
      </p>

      {/* Email */}
      <Input
        label="Votre adresse email"
        type="email"
        value={email}
        onChange={e => { setEmail(e.target.value); setError(''); }}
        placeholder="vous@entreprise.com"
        autoComplete="email"
      />

      {/* PIN */}
      <div>
        <label className="text-sm font-medium text-[#1A1A2E] block mb-2">Code PIN (4 chiffres)</label>
        <div className={`flex gap-3 justify-center ${shake ? 'animate-shake' : ''}`}>
          {digits.map((digit, i) => (
            <input
              key={i}
              ref={refs[i]}
              type="number"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={e => handleDigitChange(i, e.target.value)}
              onKeyDown={e => handleKeyDown(i, e)}
              onPaste={handlePaste}
              className={`w-[56px] h-[64px] text-center text-2xl font-bold rounded-xl border-2
                bg-white outline-none transition-all duration-200
                [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none
                ${digit ? 'border-[#1B73E8] text-[#1A1A2E]' : 'border-gray-200 text-[#1A1A2E]'}
                ${error ? 'border-red-400' : ''}
                focus:border-[#1B73E8] focus:ring-2 focus:ring-[#1B73E8]/20`}
            />
          ))}
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-500 text-center animate-fade-in">{error}</p>
      )}

      <Button
        onClick={() => handleSubmit()}
        loading={loading}
        disabled={digits.join('').length !== 4 || !email.trim() || loading}
        className="w-full"
        size="lg"
      >
        {loading ? 'Connexion...' : 'Se connecter →'}
      </Button>
    </div>
  );
}
