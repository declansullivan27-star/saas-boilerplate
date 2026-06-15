'use client';

import { ExternalLink, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { site } from './site';

/**
 * Embeds the Cal.com / Calendly booking page in a branded frame.
 * Works with any scheduling URL set in `site.bookingUrl`.
 */
export const BookingEmbed = () => {
  const [loaded, setLoaded] = useState(false);

  return (
    <div className="
      relative overflow-hidden rounded-2xl border border-border bg-card
    "
    >
      {!loaded && (
        <div className="
          absolute inset-0 flex flex-col items-center justify-center gap-3
          text-muted-foreground
        "
        >
          <Loader2 className="size-6 animate-spin text-gold" />
          <p className="text-sm">Loading the calendar…</p>
        </div>
      )}
      <iframe
        title="Book your free AI audit"
        src={site.bookingUrl}
        onLoad={() => setLoaded(true)}
        className="h-[70vh] min-h-[640px] w-full"
      />
      <div className="
        border-t border-border px-4 py-3 text-center text-sm
        text-muted-foreground
      "
      >
        Calendar not loading?
        {' '}
        <a
          href={site.bookingUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="
            inline-flex items-center gap-1 text-gold underline-offset-4
            hover:underline
          "
        >
          Open it in a new tab
          <ExternalLink className="size-3.5" />
        </a>
      </div>
    </div>
  );
};
