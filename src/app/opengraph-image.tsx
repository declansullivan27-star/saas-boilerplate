/* eslint-disable react-refresh/only-export-components -- Next.js metadata route files must export size/alt/contentType alongside the component. */
import { ImageResponse } from 'next/og';
import { site } from '@/features/autofire/site';

export const alt = 'AutoFire — AI automation that wins back your time';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

// Dynamically generated social share card (premium dark + gold).
export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: 80,
          background:
            'radial-gradient(900px 500px at 20% 0%, rgba(232,194,106,0.16), transparent), #15130F',
          color: '#F5F3EE',
          fontFamily: 'sans-serif',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 64,
              height: 64,
              borderRadius: 16,
              background: '#E8C26A',
            }}
          >
            <svg width="38" height="38" viewBox="0 0 32 32">
              <path
                d="M16 4.5c.6 3.7-1.9 5.5-3.6 7.2-1.9 1.9-3.9 3.9-3.9 7.2C8.5 23.1 11.9 26.5 16 26.5s7.5-3.4 7.5-7.6c0-2.8-1.3-4.9-2.8-6.8-.6 1.1-1.7 1.9-2.8 1.9 1.3-2.9.4-6.6-1.9-9.5z"
                fill="#15130F"
              />
            </svg>
          </div>
          <div style={{ fontSize: 38, fontWeight: 700, letterSpacing: -1 }}>{site.name}</div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              fontSize: 68,
              fontWeight: 800,
              lineHeight: 1.05,
              letterSpacing: -2,
              maxWidth: 980,
            }}
          >
            <span>Put your busywork&nbsp;</span>
            <span style={{ color: '#E8C26A' }}>on autopilot&nbsp;</span>
            <span>with AI.</span>
          </div>
          <div style={{ fontSize: 30, color: '#B8B2A6', maxWidth: 880 }}>
            Done-for-you AI chatbots, lead responders & automations for local businesses and online stores.
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div
            style={{
              display: 'flex',
              padding: '14px 28px',
              borderRadius: 12,
              background: '#E8C26A',
              color: '#15130F',
              fontSize: 28,
              fontWeight: 700,
            }}
          >
            Book your free AI audit
          </div>
          <div style={{ fontSize: 26, color: '#B8B2A6' }}>{site.domain}</div>
        </div>
      </div>
    ),
    { ...size },
  );
}
