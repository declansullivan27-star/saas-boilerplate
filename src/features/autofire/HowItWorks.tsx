import { Reveal } from './Reveal';

const steps = [
  {
    step: '01',
    title: 'Free AI audit',
    body: 'A 15-minute call where I map your biggest time-drains and show you exactly what AI can take off your plate — no jargon, no pressure.',
  },
  {
    step: '02',
    title: 'I build it for you',
    body: 'You get a tailored automation built, tested and connected to your tools — usually live within a week. You barely lift a finger.',
  },
  {
    step: '03',
    title: 'You get your time back',
    body: 'Your AI runs 24/7. I keep it tuned and improving. You focus on the work that actually grows the business.',
  },
];

export const HowItWorks = () => (
  <section
    id="how"
    className="
      mx-auto max-w-6xl scroll-mt-20 px-4 py-24
      sm:px-6
    "
  >
    <Reveal className="mx-auto max-w-2xl text-center">
      <p className="text-sm font-semibold tracking-wide text-gold uppercase">How it works</p>
      <h2 className="
        mt-3 text-3xl font-bold tracking-tight
        sm:text-4xl
      "
      >
        From overwhelmed to automated in 3 steps
      </h2>
    </Reveal>

    <div className="
      mt-14 grid gap-6
      md:grid-cols-3
    "
    >
      {steps.map((step, i) => (
        <Reveal key={step.step} delay={i * 100}>
          <div className="
            relative h-full rounded-2xl border border-border bg-card p-7
          "
          >
            <span className="text-gradient-gold text-5xl font-bold">{step.step}</span>
            <h3 className="mt-4 text-xl font-semibold">{step.title}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{step.body}</p>
          </div>
        </Reveal>
      ))}
    </div>
  </section>
);
