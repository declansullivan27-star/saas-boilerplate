import type { Metadata } from 'next';
import { setRequestLocale } from 'next-intl/server';
import { LegalShell } from '@/features/autofire/LegalShell';
import { site } from '@/features/autofire/site';

type PageProps = { params: Promise<{ locale: string }> };

export const metadata: Metadata = {
  title: `Privacy Policy — ${site.name}`,
  robots: { index: true, follow: true },
};

export default async function PrivacyPage(props: PageProps) {
  const { locale } = await props.params;
  setRequestLocale(locale);

  return (
    <LegalShell title="Privacy Policy" updated="15 June 2026">
      <p>
        This Privacy Policy explains how
        {' '}
        {site.name}
        {' '}
        ("we", "us") collects and uses your
        information when you visit our website or contact us. This is a starting
        template — please review it with a qualified professional for your
        jurisdiction before relying on it.
      </p>

      <h2>Information we collect</h2>
      <ul>
        <li>
          <strong>Information you give us:</strong>
          {' '}
          when you submit the contact form
          we collect your name, business name, email address and your message.
        </li>
        <li>
          <strong>Booking information:</strong>
          {' '}
          if you book a call, our scheduling
          provider (e.g. Cal.com or Calendly) collects your name, email and chosen time.
        </li>
        <li>
          <strong>Usage data:</strong>
          {' '}
          basic, non-identifying analytics such as pages
          visited and device type, where enabled.
        </li>
      </ul>

      <h2>How we use your information</h2>
      <ul>
        <li>To respond to your enquiry and provide our services.</li>
        <li>To schedule and conduct your free audit and any follow-up.</li>
        <li>To improve our website and offering.</li>
      </ul>

      <h2>Who we share it with</h2>
      <p>
        We do not sell your data. We share it only with the service providers that
        help us operate, such as our hosting provider (Vercel), email provider
        (e.g. Resend) and scheduling provider (e.g. Cal.com). Each processes data
        on our behalf.
      </p>

      <h2>Your rights</h2>
      <p>
        You may request access to, correction of, or deletion of your personal data
        at any time by emailing us at
        {' '}
        <a href={`mailto:${site.email}`}>{site.email}</a>
        .
      </p>

      <h2>Contact</h2>
      <p>
        Questions about this policy? Email
        {' '}
        <a href={`mailto:${site.email}`}>{site.email}</a>
        .
      </p>
    </LegalShell>
  );
}
