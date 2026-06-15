# Runbook — switch the business on

Work top to bottom. Each step is concrete. ☐ = do it.

## 1. Brand the site (15 min)
Edit **`src/features/autofire/site.ts`**:
- ☐ `bookingUrl` → your real Cal.com/Calendly link (see step 3)
- ☐ `instagramUrl` → your IG profile
- ☐ `email` → the inbox you check daily
- ☐ (optional) `name` / `domain` if you rename the agency

Then personalise **`src/features/autofire/FounderSection.tsx`** with your real name and,
if you have one, a headshot (drop it in `public/` and swap the "AF" box for an `<img>`).

## 2. Run it locally (5 min)
```bash
npm install
npm run dev        # http://localhost:3000
```
Click every button. Confirm the nav, the niche toggle, and that all CTAs land on `/book`.

## 3. Set up booking (15 min) — Cal.com (free)
1. ☐ Create an account at https://cal.com
2. ☐ Make an event type called **"Free AI Audit"**, 15 minutes
3. ☐ Connect your Google/Outlook calendar so it shows real availability
4. ☐ Copy the public link (e.g. `https://cal.com/yourname/free-ai-audit`) → paste into `site.bookingUrl`
5. ☐ (optional) Add 1–2 intake questions: "What's your business?" / "Biggest time-drain?"

## 4. Set up lead emails (10 min) — optional but recommended
The contact form already works (leads are logged). To get them by email:
1. ☐ Sign up at https://resend.com, create an API key
2. ☐ Add env vars (locally in `.env.local`, and in Vercel later):
   ```
   RESEND_API_KEY=re_xxx
   CONTACT_TO_EMAIL=you@yourdomain.com
   CONTACT_FROM_EMAIL=AutoFire <onboarding@resend.dev>
   ```
   (Use `onboarding@resend.dev` until you verify your own domain in Resend.)

## 5. Deploy (20 min) — Vercel
Full detail in **`/DEPLOY.md`**. Short version:
1. ☐ Import `declansullivan27-star/saas-boilerplate` at https://vercel.com/new
2. ☐ Add env vars: the Clerk keys, `DATABASE_URL` (free Neon DB), `NEXT_PUBLIC_APP_URL`, plus the Resend vars from step 4
3. ☐ Deploy → you get a `*.vercel.app` URL
4. ☐ (optional) Add your custom domain under Project → Domains, then set `NEXT_PUBLIC_APP_URL` to it

## 6. Set up the business basics (1–2 hrs)
- ☐ **Domain:** buy one (Namecheap/Cloudflare), ~$10/yr. Point it at Vercel.
- ☐ **Business email:** Google Workspace or Zoho on your domain.
- ☐ **Instagram:** business account, bio = one line + the `/book` link. Highlight = "Demos".
- ☐ **Payments:** Stripe account (invoices/payment links) — see OPERATIONS.md.
- ☐ **Scheduling buffer:** block focus time so audits don't swallow build time.

## 7. Learn the craft (10–20 hrs, week 1)
Build the 5 automations on a fake "demo" business first — see **DELIVERY.md**.
You must be able to demo at least: a **booking chatbot** and a **lead responder**.

## 8. Go live checklist
- ☐ Site deployed, custom domain, HTTPS green
- ☐ `/book` opens your real calendar; test-book yourself
- ☐ Contact form sends you an email (submit a test)
- ☐ OG image shows when you paste the link in a DM to yourself
- ☐ Privacy/Terms linked in footer
- ☐ 3 demo videos recorded (screen recordings of your automations working)
- ☐ Outreach list of 50 local businesses ready (see OUTREACH.md)

When all boxes are ticked, start **OUTREACH.md** and **CONTENT-CALENDAR.md** the same day.
