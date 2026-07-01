import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ChessClient } from '@/features/chess/ChessClient';

type ChessGuidePageProps = {
  params: Promise<{ locale: string }>;
};

export async function generateMetadata(props: ChessGuidePageProps): Promise<Metadata> {
  const { locale } = await props.params;
  const t = await getTranslations({ locale, namespace: 'ChessGuidePage' });

  return {
    title: t('meta_title'),
    description: t('meta_description'),
  };
}

export default async function ChessGuidePage(props: ChessGuidePageProps) {
  const { locale } = await props.params;
  setRequestLocale(locale);

  return <ChessClient />;
}
