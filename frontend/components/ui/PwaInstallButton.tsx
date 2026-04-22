'use client';
import { useEffect, useState } from 'react';

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export function PwaInstallButton() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isIOS, setIsIOS] = useState(false);
  const [showIOSInstructions, setShowIOSInstructions] = useState(false);
  const [installed, setInstalled] = useState(false);

  useEffect(() => {
    const ios = /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as Window & { MSStream?: unknown }).MSStream;
    setIsIOS(ios);

    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    if (isStandalone) { setInstalled(true); return; }

    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  if (installed) return null;
  if (!deferredPrompt && !isIOS) return null;

  const handleInstall = async () => {
    if (isIOS) {
      setShowIOSInstructions(true);
      return;
    }
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') setInstalled(true);
    setDeferredPrompt(null);
  };

  return (
    <>
      <button
        onClick={handleInstall}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-blue-200 text-blue-600 text-sm hover:bg-blue-50 transition-colors"
        title="Installer l'application"
      >
        <img src="/favicon.png?v=4" className="w-6 h-6 object-contain" alt="Pepperyn" />
        <span className="hidden sm:inline">Installer l&apos;app</span>
      </button>

      {showIOSInstructions && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50 p-4" onClick={() => setShowIOSInstructions(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm" onClick={e => e.stopPropagation()}>
            <h3 className="font-bold text-lg mb-3 text-[#1A1A2E]">Installer Pepperyn sur iPhone</h3>
            <ol className="space-y-3 text-sm text-[#5F6368]">
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">1</span>
                <span>Appuyez sur le bouton <strong className="text-[#1A1A2E]">Partager</strong> (⬆️) en bas de Safari</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">2</span>
                <span>Faites défiler et appuyez sur <strong className="text-[#1A1A2E]">&quot;Sur l&apos;écran d&apos;accueil&quot;</strong></span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">3</span>
                <span>Appuyez sur <strong className="text-[#1A1A2E]">&quot;Ajouter&quot;</strong></span>
              </li>
            </ol>
            <button onClick={() => setShowIOSInstructions(false)} className="mt-5 w-full py-3 bg-[#1B73E8] text-white rounded-xl font-medium hover:bg-[#0D47A1] transition-colors">
              Compris
            </button>
          </div>
        </div>
      )}
    </>
  );
}
