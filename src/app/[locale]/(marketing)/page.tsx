import type { Metadata } from 'next';
import { setRequestLocale } from 'next-intl/server';
import { DemoSection } from '@/features/autofire/DemoSection';
import { FaqSection } from '@/features/autofire/FaqSection';
import { FinalCta } from '@/features/autofire/FinalCta';
import { FounderSection } from '@/features/autofire/FounderSection';
import { GuaranteeSection } from '@/features/autofire/GuaranteeSection';
import { HeroSection } from '@/features/autofire/HeroSection';
import { HowItWorks } from '@/features/autofire/HowItWorks';
import { PainSection } from '@/features/autofire/PainSection';
import { PricingSection } from '@/features/autofire/PricingSection';
import { ResultsSection } from '@/features/autofire/ResultsSection';
import { ServicesSection } from '@/features/autofire/ServicesSection';
import { site } from '@/features/autofire/site';
import { SiteFooter } from '@/features/autofire/SiteFooter';
import { SiteHeader } from '@/features/autofire/SiteHeader';

type IndexProps = {
  params: Promise<{ locale: string }>;
};

export const metadata: Metadata = {
  title: `${site.name} — AI Automation Agency for Local Businesses & Online Stores`,
  description:
    'Done-for-you AI automations that answer your messages, qualify leads and handle the busywork — live in days. Book a free 15-minute AI audit.',
  openGraph: {
    title: `${site.name} — Put your busywork on autopilot with AI`,
    description:
      'AI chatbots, lead responders and workflow automation for local businesses and online stores. Free 15-minute audit.',
    type: 'website',
  },
};

export default async function Index(props: IndexProps) {
  const { locale } = await props.params;
  setRequestLocale(locale);

  return (
    <>
      <SiteHeader />
      <main>
        <HeroSection />
        <PainSection />
        <ServicesSection />
        <HowItWorks />
        <DemoSection />
        <ResultsSection />
        <GuaranteeSection />
        <FounderSection />
        <PricingSection />
        <FaqSection />
        <FinalCta />
      </main>
      <SiteFooter />
    </>
  );
};
