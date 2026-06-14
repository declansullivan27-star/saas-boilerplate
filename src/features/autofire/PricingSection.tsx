import { Check } from 'lucide-react';
import { Reveal } from './Reveal';
import { site } from './site';

const tiers = [
  {
    name: 'Starter',
    price: '$500+',
    tagline: 'One focused automation',
    features: [
      'A single AI automation, built for you',
      'Connected to your existing tools',
      'Live within ~1 week',
      '14 days of tweaks included',
    ],
    featured: false,
  },
  {
    name: 'Growth',
    price: '$2k+',
    tagline: 'A complete AI system',
    features: [
      'Multiple automations working together',
      'Chatbot + lead responder + follow-ups',
      'Full setup & team walkthrough',
      '30 days of optimisation included',
    ],
    featured: true,
  },
  {
    name: 'Retainer',
    price: '$200+/mo',
    tagline: 'Ongoing care & improvements',
    features: [
      'Monitoring, tuning & support',
      'New automations as you grow',
      'Priority response',
      'Cancel anytime',
    ],
    featured: false,
  },
];

export const PricingSection = () => (
  <section id="pricing" className="scroll-mt-20 bg-card/30 py-24">
    <div className="
      mx-auto max-w-6xl px-4
      sm:px-6
    "
    >
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-semibold tracking-wide text-gold uppercase">Pricing</p>
        <h2 className="
          mt-3 text-3xl font-bold tracking-tight
          sm:text-4xl
        "
        >
          Simple pricing. Clear ROI.
        </h2>
        <p className="mt-4 text-muted-foreground">
          Most projects pay for themselves within the first month. Your exact quote comes after your free audit.
        </p>
      </Reveal>

      <div className="
        mt-14 grid gap-6
        lg:grid-cols-3
      "
      >
        {tiers.map((tier, i) => (
          <Reveal key={tier.name} delay={i * 90}>
            <div
              className={`
                flex h-full flex-col rounded-3xl border bg-card p-8
                ${
          tier.featured
            ? `
              border-gold-soft shadow-[0_28px_60px_-30px] ring-1
              shadow-primary/50 ring-gold-soft
            `
            : 'border-border'
          }
              `}
            >
              {tier.featured && (
                <span className="
                  mb-4 inline-flex w-fit rounded-full bg-primary px-3 py-1
                  text-xs font-semibold text-primary-foreground
                "
                >
                  Most popular
                </span>
              )}
              <h3 className="text-lg font-semibold">{tier.name}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{tier.tagline}</p>
              <p className="mt-5 text-gradient-gold text-4xl font-bold">{tier.price}</p>
              <ul className="mt-6 flex-1 space-y-3 text-sm">
                {tier.features.map(feature => (
                  <li key={feature} className="flex items-start gap-2.5">
                    <Check className="mt-0.5 size-4 shrink-0 text-gold" />
                    <span className="text-muted-foreground">{feature}</span>
                  </li>
                ))}
              </ul>
              <a
                href={site.bookingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className={`
                  mt-8 inline-flex h-11 items-center justify-center rounded-xl
                  px-6 text-sm font-semibold transition-transform
                  hover:scale-[1.03]
                  ${
          tier.featured
            ? `
              bg-primary text-primary-foreground shadow-[0_0_28px_-8px]
              shadow-primary/60
            `
            : `
              border border-border bg-card text-foreground
              hover:bg-accent
            `
          }
                `}
              >
                Get started
              </a>
            </div>
          </Reveal>
        ))}
      </div>
    </div>
  </section>
);
