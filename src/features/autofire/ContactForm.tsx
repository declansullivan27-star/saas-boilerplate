'use client';

import { CheckCircle2, Loader2, Send } from 'lucide-react';
import { useState } from 'react';

type Status = 'idle' | 'submitting' | 'success' | 'error';

const inputClass
  = 'w-full rounded-lg border border-border bg-background px-4 py-2.5 text-sm outline-none transition-colors focus:border-gold-soft focus:ring-2 focus:ring-ring/40';

export const ContactForm = () => {
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState('');

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus('submitting');
    setError('');

    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());

    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error ?? 'Something went wrong. Please try again.');
      }

      setStatus('success');
      form.reset();
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    }
  };

  if (status === 'success') {
    return (
      <div className="
        flex flex-col items-center gap-3 rounded-2xl border border-gold-soft
        bg-card p-10 text-center
      "
      >
        <CheckCircle2 className="size-10 text-gold" />
        <h3 className="text-xl font-semibold">Message sent — thank you!</h3>
        <p className="max-w-sm text-sm text-muted-foreground">
          I'll get back to you personally within one business day. Talk soon.
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={onSubmit}
      className="
        space-y-4 rounded-2xl border border-border bg-card p-6
        sm:p-8
      "
    >
      {/* Honeypot — hidden from humans, catches bots. */}
      <input
        type="text"
        name="company_website"
        tabIndex={-1}
        autoComplete="off"
        className="hidden"
        aria-hidden="true"
      />

      <div className="
        grid gap-4
        sm:grid-cols-2
      "
      >
        <label className="block text-sm">
          <span className="mb-1.5 block font-medium">Your name</span>
          <input name="name" required placeholder="Jane Smith" className={inputClass} />
        </label>
        <label className="block text-sm">
          <span className="mb-1.5 block font-medium">Business name</span>
          <input name="business" placeholder="Smith & Co." className={inputClass} />
        </label>
      </div>

      <label className="block text-sm">
        <span className="mb-1.5 block font-medium">Email</span>
        <input name="email" type="email" required placeholder="jane@business.com" className={inputClass} />
      </label>

      <label className="block text-sm">
        <span className="mb-1.5 block font-medium">What would you like to automate?</span>
        <textarea
          name="message"
          required
          rows={4}
          placeholder="We miss a lot of calls and DMs after hours…"
          className={`
            ${inputClass}
            resize-y
          `}
        />
      </label>

      {status === 'error' && (
        <p className="text-sm text-destructive">{error}</p>
      )}

      <button
        type="submit"
        disabled={status === 'submitting'}
        className="
          inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl
          bg-primary px-6 text-sm font-semibold text-primary-foreground
          shadow-[0_0_28px_-8px] shadow-primary/60 transition-transform
          hover:scale-[1.02]
          disabled:opacity-60
        "
      >
        {status === 'submitting'
          ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                {' '}
                Sending…
              </>
            )
          : (
              <>
                <Send className="size-4" />
                {' '}
                Send message
              </>
            )}
      </button>
    </form>
  );
};
