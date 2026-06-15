import type { Metadata } from 'next';
import { setRequestLocale } from 'next-intl/server';
import { LegalShell } from '@/features/autofire/LegalShell';
import { site } from '@/features/autofire/site';

type PageProps = { params: Promise<{ locale: string }> };

export const metadata: Metadata = {
  title: `Terms of Service — ${site.name}`,
  robots: { index: true, follow: true },
};

export default async function TermsPage(props: PageProps) {
  const { locale } = await props.params;
  setRequestLocale(locale);

  return (
    <LegalShell title="Terms of Service" updated="15 June 2026">
      <p>
        These terms govern the services provided by
        {' '}
        {site.name}
        . This is a starting
        template — please review it with a qualified professional before relying on it.
      </p>

      <h2>Services</h2>
      <p>
        We design, build and maintain AI automations (such as chatbots, lead
        responders, content tools and workflow automations) as agreed with you in
        writing for each project.
      </p>

      <h2>Scope &amp; quotes</h2>
      <p>
        Each project's scope, deliverables, timeline and price are confirmed before
        work begins. Work outside the agreed scope may be quoted separately.
      </p>

      <h2>Payment</h2>
      <ul>
        <li>One-off projects are invoiced as agreed (commonly a deposit up front and the balance on delivery).</li>
        <li>Retainers are billed monthly in advance and can be cancelled with reasonable notice.</li>
      </ul>

      <h2>Our guarantee</h2>
      <p>
        We agree a clear, measurable outcome with you before starting. If a delivered
        automation does not meet that agreed outcome, we will work to fix it or refund
        the relevant fee, as set out in your project agreement.
      </p>

      <h2>Your responsibilities</h2>
      <p>
        You agree to provide timely access to the accounts, content and information
        needed to deliver the work, and to use the automations lawfully.
      </p>

      <h2>Intellectual property</h2>
      <p>
        On full payment, you own the configured automations and content we deliver to
        you. We retain ownership of our underlying methods, templates and tools.
      </p>

      <h2>Liability</h2>
      <p>
        To the extent permitted by law, our total liability for any project is limited
        to the fees paid for that project. We are not liable for indirect or
        consequential losses.
      </p>

      <h2>Contact</h2>
      <p>
        Questions about these terms? Email
        {' '}
        <a href={`mailto:${site.email}`}>{site.email}</a>
        .
      </p>
    </LegalShell>
  );
}
