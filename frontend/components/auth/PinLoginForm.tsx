'use client';
import { useRef, useState, KeyboardEvent, ClipboardEvent } from 'react';
import { loginWithPin } from '@/lib/api';
import { saveGuestAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';

export function PinLoginForm() {
  const [digits, setDigits] = useState(['', '', '', '']);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [shake, setShake] = useState(false);
  const ref0 = useRef<HTMLInputElement>(null);
  const ref1 = useRef<HTMLInputElement>(null);
  const ref2 = useRef<HTMLInputElement>(null);
  const ref3 = useRef<HTMLInputElement>(null);
  const refs = [ref0, ref1, ref2, ref3];
  const router = useRouter();

  const triggerShake = () => {
    setShake(true);
    setTimeout(() => setShake(false), 600);
  };

  const handleChange = (index: number, value: string) => {
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
      if (pin.length === 4) handleSubmit(pin);
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
      handleSubmit(pasted);
    }
  };

  const handleSubmit = async (pin?: string) => {
    const finalPin = pin || digits.join('');
    if (finalPin.length !== 4) return;

    setLoading(true);
    setError('');
    try {
      const data = await loginWithPin(finalPin);
      saveGuestAuth(data.access_token, data.company_id, data.plan);
      router.push('/app/chat');
    } catch {
      setError('Code incorrect. Vérifiez avec votre administrateur.');
      triggerShake();
      setDigits(['', '', '', '']);
      refs[0].current?.focus();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-6">
      <p className="text-sm text-[#5F6368] text-center">
        Entrez le code PIN de votre entreprise
      </p>

      <div className={`flex gap-4 ${shake ? 'animate-shake' : ''}`}>
        {digits.map((digit, i) => (
          <input
            key={i}
            ref={refs[i]}
            type="number"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={e => handleChange(i, e.target.value)}
            onKeyDown={e => handleKeyDown(i, e)}
            onPaste={handlePaste}
            autoFocus={i === 0}
            className={`w-[60px] h-[70px] text-center text-3xl font-bold rounded-xl border-2
              bg-white outline-none transition-all duration-200
              [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none
              ${digit ? 'border-[#1B73E8] text-[#1A1A2E]' : 'border-gray-200 text-[#1A1A2E]'}
              ${error ? 'border-red-400' : ''}
              focus:border-[#1B73E8] focus:ring-2 focus:ring-[#1B73E8]/20`}
          />
        ))}
      </div>

      {error && (
        <p className="text-sm text-red-500 text-center animate-fade-in">{error}</p>
      )}

      <Button
        onClick={() => handleSubmit()}
        loading={loading}
        disabled={digits.join('').length !== 4 || loading}
        className="w-full"
        size="lg"
      >
        {loading ? 'Connexion...' : 'Se connecter →'}
      </Button>
    </div>
  );
}
