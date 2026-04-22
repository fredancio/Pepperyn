'use client';
import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';
import { Spinner } from '@/components/ui/Spinner';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    async function checkAuth() {
      const authed = await isAuthenticated();
      if (!authed) {
        router.replace(`/login?redirect=${encodeURIComponent(pathname)}`);
      } else {
        setChecking(false);
      }
    }
    checkAuth();
  }, [pathname, router]);

  if (checking) {
    return (
      <div className="min-h-screen bg-[#EFF6FF] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Spinner size="lg" />
          <p className="text-sm text-[#5F6368]">Vérification de votre session...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
