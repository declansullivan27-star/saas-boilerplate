import { Bot, MessageSquareText, PenLine, Workflow } from 'lucide-react';
import { Reveal } from './Reveal';

const services = [
  {
    icon: Bot,
    title: 'AI Reception Chatbot',
    body: 'A 24/7 assistant on your site, Instagram and WhatsApp that answers FAQs, books appointments and never sleeps.',
    points: ['Books appointments automatically', 'Answers in your brand voice', 'Captures every after-hours lead'],
  },
  {
    icon: MessageSquareText,
    title: 'Lead Responder & Qualifier',
    body: 'Instantly replies to new enquiries, asks the right questions and hands you only the leads worth your time.',
    points: ['Replies in under a minute', 'Scores & qualifies leads', 'Pushes them to your CRM'],
  },
  {
    icon: PenLine,
    title: 'Content & Reply Engine',
    body: 'Generate captions, product descriptions and customer replies on tap — consistent, on-brand and fast.',
    points: ['Captions & posts in seconds', 'Product descriptions at scale', 'Review & DM responses'],
  },
  {
    icon: Workflow,
    title: 'Workflow Automation',
    body: 'Connect your tools so data, invoices and follow-ups move on their own. No more copy-paste between apps.',
    points: ['Auto follow-ups & reminders', 'Tools talking to each other', 'Reports without spreadsheets'],
  },
];

export const ServicesSection = () => (
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

      <div className="
        mt-14 grid gap-5
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
                {service.points.map(point => (
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
