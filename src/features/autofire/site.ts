/**
 * Central place to edit AutoFire's brand details, links and contact info.
 * Replace the TODO placeholders with your real accounts before going live.
 */
export const site = {
  name: 'AutoFire',
  domain: 'autofire.agency',
  tagline: 'AI automations that win back your time.',

  // TODO: replace with your real Cal.com / Calendly booking link.
  bookingUrl: 'https://cal.com/autofire/audit',

  // TODO: replace with your real social + contact details.
  instagramUrl: 'https://instagram.com/autofire',
  email: 'hello@autofire.agency',

  // Primary call-to-action label, reused everywhere.
  ctaLabel: 'Book your free AI audit',
} as const;

export const navLinks = [
  { label: 'Services', href: '#services' },
  { label: 'How it works', href: '#how' },
  { label: 'Pricing', href: '#pricing' },
  { label: 'FAQ', href: '#faq' },
] as const;
