import { Clock4, MailX, PhoneMissed, TrendingDown } from 'lucide-react';
import { Reveal } from './Reveal';

const pains = [
  {
    icon: PhoneMissed,
    title: 'Missed calls & DMs',
    body: 'Every unanswered message is a customer quietly walking to a competitor.',
  },
  {
    icon: MailX,
    title: 'Inbox overload',
    body: 'Hours each day spent typing the same replies and chasing no-shows.',
  },
  {
    icon: Clock4,
    title: 'No time to follow up',
    body: 'Hot leads go cold because nobody got back to them fast enough.',
  },
  {
    icon: TrendingDown,
    title: 'Manual busywork',
    body: 'Copy-pasting between tools, spreadsheets and apps instead of growing.',
  },
];

export const PainSection = () => (
  <section className="
    mx-auto max-w-6xl px-4 py-24
    sm:px-6
  "
  >
    <Reveal className="mx-auto max-w-2xl text-center">
      <p className="text-sm font-semibold tracking-wide text-gold uppercase">Sound familiar?</p>
      <h2 className="
        mt-3 text-3xl font-bold tracking-tight
        sm:text-4xl
      "
      >
        You didn't start a business to live in your inbox
      </h2>
      <p className="mt-4 text-muted-foreground">
        Most owners lose 10+ hours a week to work a well-built AI system could handle in seconds.
      </p>
    </Reveal>

    <div className="
      mt-14 grid gap-4
      sm:grid-cols-2
      lg:grid-cols-4
    "
    >
      {pains.map((pain, i) => (
        <Reveal key={pain.title} delay={i * 80}>
          <div className="
            h-full rounded-2xl border border-border bg-card p-6
            transition-colors
            hover:border-gold-soft
          "
          >
            <pain.icon className="size-7 text-gold" />
            <h3 className="mt-4 font-semibold">{pain.title}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{pain.body}</p>
          </div>
        </Reveal>
      ))}
    </div>
  </section>
);
