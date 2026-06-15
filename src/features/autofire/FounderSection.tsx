import { Reveal } from './Reveal';
import { site } from './site';

export const FounderSection = () => (
  <section className="
    mx-auto max-w-6xl px-4 py-24
    sm:px-6
  "
  >
    <div className="
      grid items-center gap-12
      lg:grid-cols-[1.2fr_1fr]
    "
    >
      <Reveal>
        <p className="text-sm font-semibold tracking-wide text-gold uppercase">Why work with me</p>
        <h2 className="
          mt-3 text-3xl font-bold tracking-tight
          sm:text-4xl
        "
        >
          Small enough to care. Fast enough to matter.
        </h2>
        <div className="mt-5 space-y-4 text-muted-foreground">
          <p>
            I'm an independent AI automation specialist — not an agency that buries you in
            account managers and six-week timelines. When you work with
            {' '}
            {site.name}
            , you
            work directly with the person building your system.
          </p>
          <p>
            That means you get answers the same day, builds that go live in days, and
            someone who genuinely cares whether this works for
            {' '}
            <span className="text-foreground">your</span>
            {' '}
            business — because my
            reputation is riding on it.
          </p>
        </div>
        <ul className="
          mt-6 grid gap-3
          sm:grid-cols-2
        "
        >
          {[
            'Direct access — no middlemen',
            'Live in days, not months',
            'Plain English, zero jargon',
            'Results-based guarantee',
          ].map(item => (
            <li key={item} className="flex items-center gap-2 text-sm">
              <span className="size-1.5 rounded-full bg-gold" />
              {item}
            </li>
          ))}
        </ul>
      </Reveal>

      <Reveal delay={120}>
        <div className="rounded-3xl border border-border bg-card p-8">
          <div className="flex items-center gap-4">
            <div className="
              flex size-16 items-center justify-center rounded-2xl bg-primary
              text-2xl font-bold text-primary-foreground
            "
            >
              AF
            </div>
            <div>
              <p className="font-semibold">
                Founder,
                {site.name}
              </p>
              <p className="text-sm text-muted-foreground">AI Automation Specialist</p>
            </div>
          </div>
          <blockquote className="
            mt-6 border-l-2 border-gold-soft pl-4 text-sm text-muted-foreground
            italic
          "
          >
            "My goal is simple: give you back the hours you're losing to busywork —
            and make the tech completely invisible to you."
          </blockquote>
        </div>
      </Reveal>
    </div>
  </section>
);
