import type { Metadata } from 'next';
import { setRequestLocale } from 'next-intl/server';
import { BookingEmbed } from '@/features/autofire/BookingEmbed';
import { ContactForm } from '@/features/autofire/ContactForm';
import { site } from '@/features/autofire/site';
import { SiteFooter } from '@/features/autofire/SiteFooter';
import { SiteHeader } from '@/features/autofire/SiteHeader';

type BookProps = {
  params: Promise<{ locale: string }>;
};

export const metadata: Metadata = {
  title: `Book your free AI audit — ${site.name}`,
  description:
    'Grab a free 15-minute AI audit. We\'ll map your biggest time-drains and show you exactly what AI can automate in your business.',
};

export default async function BookPage(props: BookProps) {
  const { locale } = await props.params;
  setRequestLocale(locale);

  return (
    <>
      <SiteHeader />
      <main className="
        mx-auto max-w-5xl px-4 pt-32 pb-24
        sm:px-6
      "
      >
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold tracking-wide text-gold uppercase">Free 15-min audit</p>
          <h1 className="
            mt-3 text-4xl font-bold tracking-tight text-balance
            sm:text-5xl
          "
          >
            Let's find your
            {' '}
            <span className="text-gradient-gold">quick wins</span>
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
            Pick a time that suits you. On the call I'll map where you're losing hours and
            show you exactly what AI can take off your plate — no jargon, no pressure.
          </p>
        </div>

        <div className="mt-12">
          <BookingEmbed />
        </div>

        <div className="mx-auto mt-20 max-w-2xl">
          <div className="text-center">
            <h2 className="text-2xl font-bold tracking-tight">Prefer to write instead?</h2>
            <p className="mt-3 text-muted-foreground">
              Send a few details and I'll reply personally within one business day.
            </p>
          </div>
          <div className="mt-8">
            <ContactForm />
          </div>
        </div>
      </main>
      <SiteFooter />
    </>
  );
};
