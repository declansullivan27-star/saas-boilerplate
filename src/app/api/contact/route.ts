import * as z from 'zod';

/**
 * Lead capture endpoint for the AutoFire contact form.
 *
 * It validates the payload, blocks bots via a honeypot, and — if a
 * RESEND_API_KEY is configured — emails the lead to you. With no key set it
 * still succeeds and logs the lead, so the form works out of the box and
 * "just works" the moment you add the env vars.
 */
const ContactSchema = z.object({
  name: z.string().min(1, 'Name is required').max(120),
  business: z.string().max(160).optional().default(''),
  email: z.string().email('A valid email is required').max(160),
  message: z.string().min(1, 'Message is required').max(4000),
  // Honeypot: must be empty.
  company_website: z.string().max(0).optional().default(''),
});

export async function POST(request: Request) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return Response.json({ error: 'Invalid request body.' }, { status: 400 });
  }

  const parsed = ContactSchema.safeParse(payload);
  if (!parsed.success) {
    // If the honeypot was filled, pretend success so bots don't learn anything.
    if ((payload as { company_website?: string })?.company_website) {
      return Response.json({ ok: true });
    }
    const error = parsed.error.issues[0]?.message ?? 'Invalid submission.';
    return Response.json({ error }, { status: 422 });
  }

  const { name, business, email, message } = parsed.data;

  const apiKey = process.env.RESEND_API_KEY;
  const to = process.env.CONTACT_TO_EMAIL;
  const from = process.env.CONTACT_FROM_EMAIL ?? 'AutoFire <onboarding@resend.dev>';

  if (apiKey && to) {
    try {
      const res = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from,
          to,
          reply_to: email,
          subject: `New AutoFire lead: ${name}${business ? ` (${business})` : ''}`,
          text: `Name: ${name}\nBusiness: ${business || '—'}\nEmail: ${email}\n\n${message}`,
        }),
      });

      if (!res.ok) {
        const detail = await res.text();
        console.error('Resend error:', detail);
        return Response.json({ error: 'Could not send your message. Please email me directly.' }, { status: 502 });
      }
    } catch (err) {
      console.error('Contact send failed:', err);
      return Response.json({ error: 'Could not send your message. Please email me directly.' }, { status: 502 });
    }
  } else {
    // No email provider configured yet — log so the lead is never lost.
    console.warn('[contact] New lead (configure RESEND_API_KEY + CONTACT_TO_EMAIL to receive emails):', {
      name,
      business,
      email,
      message,
    });
  }

  return Response.json({ ok: true });
}
