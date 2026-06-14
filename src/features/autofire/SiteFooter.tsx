import { AtSign, Flame, Mail } from 'lucide-react';
import { navLinks, site } from './site';

export const SiteFooter = () => (
  <footer className="border-t border-border">
    <div className="
      mx-auto max-w-6xl px-4 py-12
      sm:px-6
    "
    >
      <div className="
        flex flex-col items-center justify-between gap-8
        md:flex-row md:items-start
      "
      >
        <div className="
          text-center
          md:text-left
        "
        >
          <a
            href="#top"
            className="
              flex items-center justify-center gap-2 font-semibold
              md:justify-start
            "
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
          <p className="mt-3 max-w-xs text-sm text-muted-foreground">{site.tagline}</p>
        </div>

        <ul className="
          flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm
          text-muted-foreground
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

        <div className="flex items-center gap-3">
          <a
            href={site.instagramUrl}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Instagram"
            className="
              flex size-10 items-center justify-center rounded-lg border
              border-border text-muted-foreground transition-colors
              hover:border-gold-soft hover:text-gold
            "
          >
            <AtSign className="size-5" />
          </a>
          <a
            href={`mailto:${site.email}`}
            aria-label="Email"
            className="
              flex size-10 items-center justify-center rounded-lg border
              border-border text-muted-foreground transition-colors
              hover:border-gold-soft hover:text-gold
            "
          >
            <Mail className="size-5" />
          </a>
        </div>
      </div>

      <div className="
        mt-10 border-t border-border pt-6 text-center text-xs
        text-muted-foreground
      "
      >
        ©
        {' '}
        {new Date().getFullYear()}
        {' '}
        {site.name}
        . All rights reserved.
      </div>
    </div>
  </footer>
);
