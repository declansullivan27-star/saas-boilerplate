import { ShieldCheck } from 'lucide-react';
import { Reveal } from './Reveal';

export const GuaranteeSection = () => (
  <section className="
    mx-auto max-w-6xl px-4 py-12
    sm:px-6
  "
  >
    <Reveal>
      <div className="
        relative overflow-hidden rounded-3xl border border-gold-soft bg-card p-8
        text-center
        sm:p-12
      "
      >
        <div className="
          pointer-events-none absolute inset-0 bg-aurora opacity-60
        "
        />
        <div className="relative">
          <span className="
            mx-auto flex size-14 items-center justify-center rounded-2xl
            bg-primary/10 text-gold ring-1 ring-gold-soft
          "
          >
            <ShieldCheck className="size-7" />
          </span>
          <h2 className="
            mt-6 text-2xl font-bold tracking-tight
            sm:text-3xl
          "
          >
            If it doesn't save you time, you don't pay.
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
            I'm betting on results, not promises. We agree on a clear outcome before we start —
            and if the automation doesn't deliver it, you get your money back. Simple as that.
          </p>
        </div>
      </div>
    </Reveal>
  </section>
);
