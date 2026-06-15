import { Clock, MessageSquare, TrendingUp } from 'lucide-react';
import { Reveal } from './Reveal';

/**
 * Illustrative "results" cards. These are example outcomes, not real client
 * data — clearly labelled as such. Replace with real case studies (and drop
 * the disclaimer) as soon as you have your first results.
 */
const results = [
  {
    icon: Clock,
    metric: '12 hrs',
    label: 'saved per week',
    context: 'A salon automated booking + reminders and stopped fielding calls during appointments.',
  },
  {
    icon: MessageSquare,
    metric: '< 60 sec',
    label: 'reply time, 24/7',
    context: 'An online store added an AI assistant that answers product & shipping questions instantly.',
  },
  {
    icon: TrendingUp,
    metric: '3x',
    label: 'more booked leads',
    context: 'A home-services business let AI qualify and follow up with every new enquiry automatically.',
  },
];

export const ResultsSection = () => (
  <section className="
    mx-auto max-w-6xl px-4 py-24
    sm:px-6
  "
  >
    <Reveal className="mx-auto max-w-2xl text-center">
      <p className="text-sm font-semibold tracking-wide text-gold uppercase">What good looks like</p>
      <h2 className="
        mt-3 text-3xl font-bold tracking-tight
        sm:text-4xl
      "
      >
        The kind of results AI can deliver
      </h2>
      <p className="mt-4 text-muted-foreground">
        Example outcomes from the automations I build. Your numbers depend on your business —
        we'll estimate yours on the free audit.
      </p>
    </Reveal>

    <div className="
      mt-14 grid gap-5
      md:grid-cols-3
    "
    >
      {results.map((result, i) => (
        <Reveal key={result.label} delay={i * 90}>
          <div className="h-full rounded-2xl border border-border bg-card p-7">
            <result.icon className="size-7 text-gold" />
            <p className="mt-5 text-gradient-gold text-4xl font-bold">{result.metric}</p>
            <p className="text-sm font-medium">{result.label}</p>
            <p className="mt-3 text-sm text-muted-foreground">{result.context}</p>
          </div>
        </Reveal>
      ))}
    </div>

    <Reveal className="mt-8 text-center">
      <p className="text-xs text-muted-foreground">
        * Illustrative examples for demonstration, not guarantees of specific results.
      </p>
    </Reveal>
  </section>
);
