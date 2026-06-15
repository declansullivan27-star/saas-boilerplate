# Deploying AutoFire

The site is a Next.js 16 app and deploys best on **Vercel**.

## 1. Before you deploy — edit your details

Open `src/features/autofire/site.ts` and replace the placeholders:

- `bookingUrl` — your real Cal.com or Calendly link (embedded on `/book`)
- `instagramUrl` — your Instagram profile
- `email` — your contact email

(Optional) Personalise `src/features/autofire/FounderSection.tsx` with your name/photo.

## 2. Push to GitHub

Already done — the code lives on your repo. Vercel deploys straight from it.

## 3. Create the Vercel project

1. Go to https://vercel.com/new and import `declansullivan27-star/saas-boilerplate`.
2. Framework preset: **Next.js** (auto-detected). No build settings to change.
3. Add the environment variables below, then **Deploy**.

## 4. Environment variables

### Required (the boilerplate validates these at build time)

| Variable | What it is | Where to get it |
| --- | --- | --- |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk auth (used by the kept dashboard) | https://clerk.com |
| `CLERK_SECRET_KEY` | Clerk secret | https://clerk.com |
| `DATABASE_URL` | Postgres connection string | A free Neon DB: https://neon.tech |
| `NEXT_PUBLIC_APP_URL` | Your production URL, e.g. `https://autofire.agency` | — |

> The marketing site itself doesn't use the DB, but the boilerplate's env
> schema requires `DATABASE_URL` and the Clerk keys to be present at build.

### Optional — lead emails from the contact form

| Variable | What it is |
| --- | --- |
| `RESEND_API_KEY` | Resend API key (https://resend.com) |
| `CONTACT_TO_EMAIL` | The inbox that receives leads |
| `CONTACT_FROM_EMAIL` | From address (defaults to `AutoFire <onboarding@resend.dev>`) |

Without these the form still works — leads are logged to the server console
so nothing is lost — but you won't get an email until you add them.

## 5. Point your domain

In Vercel → Project → **Domains**, add your domain (e.g. `autofire.agency`)
and follow the DNS instructions. Set `NEXT_PUBLIC_APP_URL` to match.

## Run locally

```bash
npm install
npm run dev   # http://localhost:3000
```
