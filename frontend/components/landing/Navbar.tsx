'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';

const NAV_LINKS = [
  { href: '#livrables', label: 'Livrables' },
  { href: '#securite', label: 'Sécurité' },
  { href: '#tarifs', label: 'Tarifs' },
  { href: '#faq', label: 'FAQ' },
];

export function Navbar() {
  const [open, setOpen] = useState(false);

  // Ferme le menu si on redimensionne vers desktop
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 768px)');
    const close = () => { if (mq.matches) setOpen(false); };
    mq.addEventListener('change', close);
    return () => mq.removeEventListener('change', close);
  }, []);

  // Empêche le scroll body quand le menu mobile est ouvert
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  return (
    <>
      <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">

          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 flex-shrink-0" onClick={() => setOpen(false)}>
            <img src="/favicon.png?v=5" alt="Pepperyn" className="w-9 h-9 object-contain" />
            <div>
              <span className="text-base font-bold text-[#1A1A2E] block leading-none">Pepperyn</span>
              <span className="text-[10px] text-[#5F6368] block hidden sm:block leading-none mt-0.5">
                Financial Operating System
              </span>
            </div>
          </Link>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-6">
            {NAV_LINKS.map(l => (
              <Link
                key={l.href}
                href={l.href}
                className="text-sm text-[#5F6368] hover:text-[#1A1A2E] transition-colors"
              >
                {l.label}
              </Link>
            ))}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-2">
            {/* Se connecter — masqué sur très petit écran */}
            <Link
              href="/login"
              className="hidden sm:inline-flex items-center px-4 py-2 border border-[#1B73E8] text-[#1B73E8] text-sm font-semibold rounded-xl hover:bg-blue-50 transition-all duration-200"
            >
              Se connecter
            </Link>

            {/* CTA principal */}
            <Link
              href="/register"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#1B73E8] text-white text-sm font-semibold rounded-xl hover:bg-[#0D47A1] transition-all duration-200 shadow-sm"
            >
              <span className="hidden sm:inline">Essai gratuit</span>
              <span className="sm:hidden">Démarrer</span>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>

            {/* Hamburger — visible uniquement < md */}
            <button
              onClick={() => setOpen(v => !v)}
              className="md:hidden w-9 h-9 flex items-center justify-center rounded-lg text-[#5F6368] hover:bg-gray-100 transition-colors flex-shrink-0"
              aria-label={open ? 'Fermer le menu' : 'Ouvrir le menu'}
              aria-expanded={open}
            >
              {open ? (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Menu mobile déroulant */}
        {open && (
          <div className="md:hidden border-t border-gray-100 bg-white shadow-lg">
            <div className="max-w-7xl mx-auto px-4 py-3 flex flex-col gap-1">
              {NAV_LINKS.map(l => (
                <Link
                  key={l.href}
                  href={l.href}
                  onClick={() => setOpen(false)}
                  className="flex items-center px-4 py-3.5 text-sm font-medium text-[#1A1A2E] hover:bg-[#EFF6FF] hover:text-[#1B73E8] rounded-xl transition-colors"
                >
                  {l.label}
                </Link>
              ))}
              <div className="h-px bg-gray-100 my-1" />
              <Link
                href="/login"
                onClick={() => setOpen(false)}
                className="flex items-center px-4 py-3.5 text-sm font-semibold text-[#1B73E8] hover:bg-blue-50 rounded-xl transition-colors"
              >
                Se connecter
              </Link>
              <Link
                href="/register"
                onClick={() => setOpen(false)}
                className="flex items-center justify-center gap-2 px-4 py-3.5 bg-[#1B73E8] text-white text-sm font-bold rounded-xl hover:bg-[#0D47A1] transition-colors mt-1 mb-1"
              >
                Essai gratuit — sans carte bancaire
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
            </div>
          </div>
        )}
      </nav>
    </>
  );
}
