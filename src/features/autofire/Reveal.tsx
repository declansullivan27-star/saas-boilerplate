'use client';

import { useEffect, useRef, useState } from 'react';
import { cn } from '@/utils/Helpers';

type RevealProps = {
  children: React.ReactNode;
  className?: string;
  /** Delay the entrance, in milliseconds, for nice staggering. */
  delay?: number;
  as?: React.ElementType;
};

/**
 * Fades + slides its children up when they scroll into view.
 * Respects prefers-reduced-motion by simply showing content immediately.
 */
export const Reveal = ({ children, className, delay = 0, as: Tag = 'div' }: RevealProps) => {
  const ref = useRef<HTMLElement | null>(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) {
      return;
    }

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setShown(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setShown(true);
          observer.disconnect();
        }
      },
      { threshold: 0.15, rootMargin: '0px 0px -40px 0px' },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <Tag
      ref={ref}
      style={{ transitionDelay: `${delay}ms` }}
      className={cn(
        'translate-y-8 opacity-0 transition-all duration-700 ease-out',
        shown && 'translate-y-0 opacity-100',
        className,
      )}
    >
      {children}
    </Tag>
  );
};
