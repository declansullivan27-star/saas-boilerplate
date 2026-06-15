'use client';

import { Bot, Building2, MessageSquareText, PenLine, ShoppingBag, Workflow } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/utils/Helpers';
import { Reveal } from './Reveal';

type Niche = 'local' | 'store';

const niches = [
  { id: 'local' as const, label: 'Local business', icon: Building2 },
  { id: 'store' as const, label: 'Online store', icon: ShoppingBag },
];

const services = [
  {
    icon: Bot,
    title: 'AI Reception Chatbot',
    body: 'A 24/7 assistant on your site, Instagram and WhatsApp that answers questions and never sleeps.',
    points: {
      local: ['Books appointments automatically', 'Answers FAQs in your brand voice', 'Captures every after-hours call & DM'],
      store: ['Answers product & shipping questions', 'Recovers carts with instant replies', 'Supports customers 24/7 everywhere'],
    },
  },
  {
    icon: MessageSquareText,
    title: 'Lead Responder & Qualifier',
    body: 'Instantly replies to new enquiries, asks the right questions and surfaces only the ones worth your time.',
    points: {
      local: ['Replies to enquiries in under a minute', 'Qualifies & books the right jobs', 'Drops leads straight on your calendar'],
      store: ['Replies to DMs & emails instantly', 'Recommends the right product', 'Nudges buyers to checkout'],
    },
  },
  {
    icon: PenLine,
    title: 'Content & Reply Engine',
    body: 'Generate on-brand copy and customer replies on tap — consistent, fast and always in your voice.',
    points: {
      local: ['Social captions & posts in seconds', 'Review responses on autopilot', 'On-brand replies every time'],
      store: ['Product descriptions at scale', 'SEO copy & ad variations', 'Review & DM responses'],
    },
  },
  {
    icon: Workflow,
    title: 'Workflow Automation',
    body: 'Connect your tools so data, follow-ups and admin move on their own. No more copy-paste between apps.',
    points: {
      local: ['Auto follow-ups & reminders', 'Tools talking to each other', 'Reports without spreadsheets'],
      store: ['Order & inventory sync', 'Abandoned-cart & post-purchase flows', 'Reports without spreadsheets'],
    },
  },
];

export const ServicesSection = () => {
  const [niche, setNiche] = useState<Niche>('local');

  return (
    <section id="services" className="scroll-mt-20 bg-card/30 py-24">
      <div className="
        mx-auto max-w-6xl px-4
        sm:px-6
      "
      >
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold tracking-wide text-gold uppercase">What I build</p>
          <h2 className="
            mt-3 text-3xl font-bold tracking-tight
            sm:text-4xl
          "
          >
            Quick wins that pay for themselves
          </h2>
          <p className="mt-4 text-muted-foreground">
            Pick one to start, or stack them into a system. Every build is tailored to how your business actually runs.
          </p>
        </Reveal>

        {/* Niche switcher */}
        <Reveal className="mt-8 flex justify-center">
          <div className="
            inline-flex items-center gap-1 rounded-xl border border-border
            bg-card p-1
          "
          >
            {niches.map(option => (
              <button
                key={option.id}
                type="button"
                onClick={() => setNiche(option.id)}
                className={cn(
                  `
                    inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm
                    font-medium transition-colors
                  `,
                  niche === option.id
                    ? 'bg-primary text-primary-foreground'
                    : `
                      text-muted-foreground
                      hover:text-foreground
                    `,
                )}
              >
                <option.icon className="size-4" />
                {option.label}
              </button>
            ))}
          </div>
        </Reveal>

        <div className="
          mt-12 grid gap-5
          md:grid-cols-2
        "
        >
          {services.map((service, i) => (
            <Reveal key={service.title} delay={i * 90}>
              <div className="
                group h-full rounded-2xl border border-border bg-card p-7
                transition-all
                hover:-translate-y-1 hover:border-gold-soft
                hover:shadow-[0_24px_48px_-24px] hover:shadow-primary/40
              "
              >
                <div className="
                  flex size-12 items-center justify-center rounded-xl
                  bg-primary/10 text-gold ring-1 ring-gold-soft
                "
                >
                  <service.icon className="size-6" />
                </div>
                <h3 className="mt-5 text-xl font-semibold">{service.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{service.body}</p>
                <ul className="mt-5 space-y-2 text-sm">
                  {service.points[niche].map(point => (
                    <li
                      key={point}
                      className="flex items-center gap-2 text-muted-foreground"
                    >
                      <span className="size-1.5 rounded-full bg-gold" />
                      {point}
                    </li>
                  ))}
                </ul>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
};
