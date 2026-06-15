import { Bot, User } from 'lucide-react';
import { Reveal } from './Reveal';
import { site } from './site';

/**
 * Placeholder "live demo" — a styled mock chat that sells the outcome.
 * Milestone 5+ can swap this for a real embedded chatbot.
 */
const messages = [
  { from: 'user', text: 'Hi, are you open Sunday and how much is a cut?' },
  { from: 'bot', text: 'Hey! Yes — we’re open Sun 10am–4pm. A cut is $35. Want me to book you in?' },
  { from: 'user', text: 'Yes please, 2pm if you have it' },
  { from: 'bot', text: 'Done ✅ You’re booked Sun 2pm. I’ll text a reminder the day before!' },
];

export const DemoSection = () => (
  <section className="
    mx-auto max-w-6xl px-4 py-24
    sm:px-6
  "
  >
    <div className="
      grid items-center gap-12
      lg:grid-cols-2
    "
    >
      <Reveal>
        <p className="text-sm font-semibold tracking-wide text-gold uppercase">See it in action</p>
        <h2 className="
          mt-3 text-3xl font-bold tracking-tight
          sm:text-4xl
        "
        >
          This is what your customers will experience
        </h2>
        <p className="mt-4 text-muted-foreground">
          No more "we'll get back to you." Your AI replies instantly, books the job
          and follows up — even at 11pm on a Sunday. On your audit call, I'll show you
          a live version trained on
          {' '}
          <span className="text-foreground">your</span>
          {' '}
          business.
        </p>
        <a
          href={site.bookingPath}
          className="
            mt-7 inline-flex h-11 items-center rounded-xl bg-primary px-6
            text-sm font-semibold text-primary-foreground shadow-[0_0_28px_-8px]
            shadow-primary/60 transition-transform
            hover:scale-[1.03]
          "
        >
          {site.ctaLabel}
        </a>
      </Reveal>

      <Reveal delay={120}>
        <div className="
          rounded-3xl border border-border bg-card p-4 shadow-2xl
          shadow-black/40
        "
        >
          <div className="
            flex items-center gap-2 border-b border-border px-3 pb-3
          "
          >
            <span className="
              flex size-7 items-center justify-center rounded-full bg-primary
              text-primary-foreground
            "
            >
              <Bot className="size-4" />
            </span>
            <span className="text-sm font-medium">
              {site.name}
              {' '}
              Assistant
            </span>
            <span className="
              ml-auto inline-flex items-center gap-1.5 text-xs
              text-muted-foreground
            "
            >
              <span className="size-2 rounded-full bg-emerald-400" />
              Online
            </span>
          </div>

          <div className="space-y-3 p-3">
            {messages.map(message => (
              <div
                key={message.text}
                className={message.from === 'user'
                  ? 'flex justify-end'
                  : `flex justify-start`}
              >
                <div
                  className={
                    message.from === 'user'
                      ? 'flex max-w-[80%] items-end gap-2'
                      : `
                        flex max-w-[80%] flex-row-reverse items-end justify-end
                        gap-2
                      `
                  }
                >
                  <span className="
                    flex size-6 shrink-0 items-center justify-center
                    rounded-full bg-muted text-muted-foreground
                  "
                  >
                    {message.from === 'user'
                      ? <User className="size-3.5" />
                      : (
                          <Bot className="size-3.5" />
                        )}
                  </span>
                  <div
                    className={
                      message.from === 'user'
                        ? `
                          rounded-2xl rounded-br-sm bg-secondary px-4 py-2.5
                          text-sm
                        `
                        : `
                          rounded-2xl rounded-bl-sm bg-primary px-4 py-2.5
                          text-sm text-primary-foreground
                        `
                    }
                  >
                    {message.text}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Reveal>
    </div>
  </section>
);
