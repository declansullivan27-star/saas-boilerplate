import { ArrowRight } from 'lucide-react';
import { Reveal } from './Reveal';
import { site } from './site';

export const FinalCta = () => (
  <section
    id="book"
    className="
      scroll-mt-20 px-4 py-24
      sm:px-6
    "
  >
    <Reveal className="mx-auto max-w-4xl">
      <div className="
        relative overflow-hidden rounded-4xl border border-gold-soft bg-card
        px-6 py-16 text-center
        sm:px-12
      "
      >
        <div className="pointer-events-none absolute inset-0 bg-aurora" />
        <div className="relative">
          <h2 className="
            mx-auto max-w-2xl text-3xl font-bold tracking-tight text-balance
            sm:text-5xl
          "
          >
            Ready to put your busywork
            {' '}
            <span className="text-gradient-gold">on autopilot?</span>
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-muted-foreground">
            Book a free 15-minute audit. I'll show you exactly what AI can automate in your
            business — and what it's worth to you. No pressure, no jargon.
          </p>
          <a
            href={site.bookingPath}
            className="
              group mt-9 inline-flex h-13 items-center justify-center gap-2
              rounded-xl bg-primary px-8 text-base font-semibold
              text-primary-foreground shadow-[0_0_44px_-8px] shadow-primary/70
              transition-transform
              hover:scale-[1.03]
            "
          >
            {site.ctaLabel}
            <ArrowRight className="
              size-5 transition-transform
              group-hover:translate-x-1
            "
            />
          </a>
          <p className="mt-4 text-sm text-muted-foreground">
            Prefer to chat first?
            {' '}
            <a
              className="
                text-gold underline-offset-4
                hover:underline
              "
              href={site.instagramUrl}
              target="_blank"
              rel="noopener noreferrer"
            >
              DM me on Instagram
            </a>
          </p>
        </div>
      </div>
    </Reveal>
  </section>
);
