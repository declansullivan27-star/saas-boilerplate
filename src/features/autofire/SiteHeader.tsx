'use client';

import { Flame, Menu, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { cn } from '@/utils/Helpers';
import { navLinks, site } from './site';

export const SiteHeader = () => {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={cn(
        'fixed inset-x-0 top-0 z-50 transition-all duration-300',
        scrolled
          ? 'border-b border-border glass'
          : `border-b border-transparent`,
      )}
    >
      <nav className="
        mx-auto flex h-16 max-w-6xl items-center justify-between px-4
        sm:px-6
      "
      >
        <a
          href="#top"
          className="flex items-center gap-2 font-semibold tracking-tight"
        >
          <span className="
            flex size-8 items-center justify-center rounded-lg bg-primary
            text-primary-foreground
          "
          >
            <Flame className="size-5" />
          </span>
          <span className="text-lg">{site.name}</span>
        </a>

        <ul className="
          hidden items-center gap-8 text-sm text-muted-foreground
          md:flex
        "
        >
          {navLinks.map(link => (
            <li key={link.href}>
              <a
                className="
                  transition-colors
                  hover:text-foreground
                "
                href={link.href}
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>

        <div className="
          hidden
          md:block
        "
        >
          <a
            href={site.bookingPath}
            className="
              inline-flex h-10 items-center rounded-lg bg-primary px-5 text-sm
              font-semibold text-primary-foreground shadow-[0_0_24px_-6px]
              shadow-primary/60 transition-transform
              hover:scale-[1.03]
            "
          >
            {site.ctaLabel}
          </a>
        </div>

        <button
          type="button"
          aria-label="Toggle menu"
          className="md:hidden"
          onClick={() => setOpen(o => !o)}
        >
          {open ? <X className="size-6" /> : <Menu className="size-6" />}
        </button>
      </nav>

      {open && (
        <div className="
          border-t border-border glass
          md:hidden
        "
        >
          <ul className="flex flex-col gap-1 p-4 text-sm">
            {navLinks.map(link => (
              <li key={link.href}>
                <a
                  className="
                    block rounded-md px-3 py-2 text-muted-foreground
                    hover:bg-accent hover:text-foreground
                  "
                  href={link.href}
                  onClick={() => setOpen(false)}
                >
                  {link.label}
                </a>
              </li>
            ))}
            <li className="mt-2">
              <a
                href={site.bookingPath}
                className="
                  block rounded-lg bg-primary p-3 text-center font-semibold
                  text-primary-foreground
                "
                onClick={() => setOpen(false)}
              >
                {site.ctaLabel}
              </a>
            </li>
          </ul>
        </div>
      )}
    </header>
  );
};
