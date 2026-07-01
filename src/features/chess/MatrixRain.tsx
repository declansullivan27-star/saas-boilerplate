'use client';

import { useEffect, useRef } from 'react';

const GLYPHS = '01アイウエオカキクケコサシスセソ♔♕♖♗♘♙♚♛♜♝♞♟'.split('');

/** Decorative falling-code background for the Chess Guide Buddy pages. Purely visual, ignores pointer events. */
export function MatrixRain() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      return;
    }

    const fontSize = 16;
    let columns = 0;
    let drops: number[] = [];

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      columns = Math.floor(canvas.width / fontSize);
      drops = Array.from({ length: columns }, () => Math.random() * -100);
    };
    resize();

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(canvas);

    let frame = 0;
    let animationId: number;

    const draw = () => {
      frame += 1;
      animationId = requestAnimationFrame(draw);
      if (frame % 2 !== 0) {
        return;
      }

      ctx.fillStyle = 'rgba(7, 12, 9, 0.18)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.font = `${fontSize}px var(--font-mono, monospace)`;
      for (let i = 0; i < columns; i++) {
        const glyph = GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
        const y = drops[i]! * fontSize;

        ctx.fillStyle = 'rgba(60, 255, 130, 0.9)';
        ctx.fillText(glyph!, i * fontSize, y);

        if (y > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
        } else {
          drops[i] = drops[i]! + 1;
        }
      }
    };
    animationId = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animationId);
      resizeObserver.disconnect();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 size-full opacity-25"
    />
  );
}
