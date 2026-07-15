'use client';

/**
 * Retired. The three parallel import modes that lived here (Standard template /
 * Universal AI / Quick AI) are superseded by the Data Hub → Smart Import funnel,
 * which handles the CLIMATRIX template deterministically and any foreign file
 * via the AI path. Old bookmarks and links land in the hub.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function ImportRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/hub');
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center gap-2 text-cy-faint">
      <Loader2 className="h-5 w-5 animate-spin" />
      Taking you to the Data Hub…
    </div>
  );
}
