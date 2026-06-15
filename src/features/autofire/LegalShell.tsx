import { SiteFooter } from './SiteFooter';
import { SiteHeader } from './SiteHeader';

/**
 * Shared layout + typography for the legal pages (privacy, terms).
 */
export const LegalShell = ({
  title,
  updated,
  children,
}: {
  title: string;
  updated: string;
  children: React.ReactNode;
}) => (
  <>
    <SiteHeader />
    <main className="
      mx-auto max-w-3xl px-4 pt-32 pb-24
      sm:px-6
    "
    >
      <h1 className="text-4xl font-bold tracking-tight">{title}</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Last updated:
        {' '}
        {updated}
      </p>
      <div className="
        mt-10 space-y-4 text-muted-foreground
        [&_a]:text-gold [&_a]:underline-offset-4
        hover:[&_a]:underline
        [&_h2]:mt-10 [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-foreground
        [&_li]:ml-5 [&_li]:list-disc
        [&_strong]:text-foreground
      "
      >
        {children}
      </div>
    </main>
    <SiteFooter />
  </>
);
