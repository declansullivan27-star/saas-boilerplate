import { ArrowRight, Clock, ShieldCheck, Sparkles } from 'lucide-react';
import { Reveal } from './Reveal';
import { site } from './site';

const stats = [
  { value: '10+ hrs', label: 'saved per week' },
  { value: '< 7 days', label: 'to go live' },
  { value: '24/7', label: 'AI working for you' },
];

export const HeroSection = () => (
  <section id="top" className="relative overflow-hidden">
    {/* Animated aurora glow */}
    <div className="pointer-events-none absolute inset-0 bg-aurora" />
    <div className="
      pointer-events-none absolute inset-0
      bg-[radial-gradient(ellipse_at_top,transparent_40%,var(--background)_100%)]
    "
    />

    <div className="
      relative mx-auto max-w-6xl px-4 pt-36 pb-24 text-center
      sm:px-6 sm:pt-44 sm:pb-32
    "
    >
      <Reveal>
        <span className="
          inline-flex items-center gap-2 rounded-full border border-gold-soft
          bg-card/60 px-4 py-1.5 text-xs font-medium text-muted-foreground
        "
        >
          <Sparkles className="size-3.5 text-gold" />
          AI automation for local businesses & online stores
        </span>
      </Reveal>

      <Reveal delay={80}>
        <h1 className="
          mx-auto mt-6 max-w-4xl text-4xl font-bold tracking-tight text-balance
          sm:text-6xl
        "
        >
          Put your busywork
          {' '}
          <span className="text-gradient-gold">on autopilot</span>
          {' '}
          with AI.
        </h1>
      </Reveal>

      <Reveal delay={160}>
        <p className="
          mx-auto mt-6 max-w-2xl text-lg text-pretty text-muted-foreground
        "
        >
          I build done-for-you AI systems that answer your messages, qualify leads
          and handle the repetitive work — so you stop losing hours (and customers)
          to your inbox. Live in days, not months.
        </p>
      </Reveal>

      <Reveal delay={240}>
        <div className="
          mt-9 flex flex-col items-center justify-center gap-3
          sm:flex-row
        "
        >
          <a
            href={site.bookingPath}
            className="
              group inline-flex h-12 w-full items-center justify-center gap-2
              rounded-xl bg-primary px-7 text-base font-semibold
              text-primary-foreground shadow-[0_0_36px_-8px] shadow-primary/70
              transition-transform
              hover:scale-[1.03]
              sm:w-auto
            "
          >
            {site.ctaLabel}
            <ArrowRight className="
              size-5 transition-transform
              group-hover:translate-x-1
            "
            />
          </a>
          <a
            href="#services"
            className="
              inline-flex h-12 w-full items-center justify-center rounded-xl
              border border-border bg-card/40 px-7 text-base font-medium
              text-foreground transition-colors
              hover:bg-accent
              sm:w-auto
            "
          >
            See what I automate
          </a>
        </div>
      </Reveal>

      <Reveal delay={320}>
        <div className="
          mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2
          text-sm text-muted-foreground
        "
        >
          <span className="inline-flex items-center gap-1.5">
            <Clock className="size-4 text-gold" />
            Free 15-min audit
          </span>
          <span className="inline-flex items-center gap-1.5">
            <ShieldCheck className="size-4 text-gold" />
            No long contracts — cancel anytime
          </span>
        </div>
      </Reveal>

      <Reveal delay={400}>
        <dl className="
          mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-px overflow-hidden
          rounded-2xl border border-border bg-border
          sm:grid-cols-3
        "
        >
          {stats.map(stat => (
            <div key={stat.label} className="bg-card px-6 py-7">
              <dt className="text-gradient-gold text-3xl font-bold">{stat.value}</dt>
              <dd className="mt-1 text-sm text-muted-foreground">{stat.label}</dd>
            </div>
          ))}
        </dl>
      </Reveal>
    </div>
  </section>
);
