import { Plus } from 'lucide-react';
import { Reveal } from './Reveal';

const faqs = [
  {
    q: 'How much does this cost?',
    a: 'Projects start around $500 for a single automation and scale based on complexity. Ongoing retainers start at $200/mo. You get an exact quote after your free audit — no surprises.',
  },
  {
    q: 'How long until it\'s live?',
    a: 'Most single automations go live within about a week. Larger systems take a little longer, but you\'ll have a clear timeline before we start.',
  },
  {
    q: 'Will the AI sound robotic?',
    a: 'No. Everything is built in your brand voice and reviewed with you. The goal is for customers to feel looked after — not like they\'re talking to a machine.',
  },
  {
    q: 'Is my data safe?',
    a: 'Yes. I use reputable, secure providers, only connect the tools you approve, and never share your data. We can sign an agreement if you\'d like.',
  },
  {
    q: 'I\'m not techy at all — is that a problem?',
    a: 'Not even slightly. That\'s the whole point. I handle the setup and explain everything in plain English. You just enjoy the results.',
  },
  {
    q: 'What if it doesn\'t work for my business?',
    a: 'We agree on a clear outcome up front. If the automation doesn\'t deliver it, you get your money back. The free audit also makes sure it\'s a fit before you spend anything.',
  },
];

export const FaqSection = () => (
  <section
    id="faq"
    className="
      mx-auto max-w-3xl scroll-mt-20 px-4 py-24
      sm:px-6
    "
  >
    <Reveal className="text-center">
      <p className="text-sm font-semibold tracking-wide text-gold uppercase">FAQ</p>
      <h2 className="
        mt-3 text-3xl font-bold tracking-tight
        sm:text-4xl
      "
      >
        Questions, answered
      </h2>
    </Reveal>

    <div className="mt-12 space-y-3">
      {faqs.map((faq, i) => (
        <Reveal key={faq.q} delay={i * 50}>
          <details className="
            group rounded-2xl border border-border bg-card p-5
            [&_summary::-webkit-details-marker]:hidden
          "
          >
            <summary className="
              flex cursor-pointer items-center justify-between gap-4 font-medium
            "
            >
              {faq.q}
              <Plus className="
                size-5 shrink-0 text-gold transition-transform
                group-open:rotate-45
              "
              />
            </summary>
            <p className="mt-3 text-sm text-muted-foreground">{faq.a}</p>
          </details>
        </Reveal>
      ))}
    </div>
  </section>
);
