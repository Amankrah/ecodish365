'use client';

// Catastrophic root-layout error boundary. Renders only when the root
// layout itself throws (root error.tsx cannot catch that). Must include
// its own <html> and <body> because the layout is replaced.

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Root layout error:', error);
  }, [error]);

  return (
    <html lang="en">
      <body style={{
        fontFamily: 'system-ui, sans-serif',
        margin: 0,
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#F8FAFC',
        color: '#0F172A',
      }}>
        <div style={{
          maxWidth: '28rem',
          padding: '2rem',
          background: 'white',
          border: '1px solid #FCD34D',
          borderRadius: '1rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        }}>
          <h1 style={{ fontSize: '1.125rem', fontWeight: 600, margin: '0 0 0.5rem' }}>
            The platform hit a critical error.
          </h1>
          <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: '#334155', margin: '0 0 1rem' }}>
            Something failed at the root of the application. Reloading usually fixes it.
            If it keeps happening, the issue is likely server-side; please come back in a
            few minutes.
          </p>
          {error.digest && (
            <p style={{ fontSize: '0.75rem', color: '#64748B', fontFamily: 'monospace', wordBreak: 'break-all', margin: '0 0 1rem' }}>
              Reference: {error.digest}
            </p>
          )}
          <button
            type="button"
            onClick={reset}
            style={{
              padding: '0.5rem 1rem',
              fontSize: '0.875rem',
              fontWeight: 600,
              color: 'white',
              background: 'linear-gradient(to right, #4F46E5, #2563EB)',
              border: 'none',
              borderRadius: '0.5rem',
              cursor: 'pointer',
            }}
          >
            Reload
          </button>
        </div>
      </body>
    </html>
  );
}
