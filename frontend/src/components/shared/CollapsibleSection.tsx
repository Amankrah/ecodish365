/**
 * CollapsibleSection — small wrapper that gives any panel a clickable
 * header with a chevron + optionally persists its collapse state in
 * localStorage keyed by `persistKey`.
 *
 * Used to collapse the per-scorer "Build Your Meal / Add Foods" picker
 * (which can dominate the page when the user already has a 20+ food list
 * pre-populated via the cross-page FoodListPanel).
 */
'use client';

import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface Props {
  title: string;
  /** Optional icon (already coloured) rendered to the left of the title. */
  icon?: ReactNode;
  /** Optional small label rendered to the right (e.g. "21 foods selected"). */
  badge?: ReactNode;
  /** localStorage key for collapse state. Omit to use ephemeral state. */
  persistKey?: string;
  /** Initial collapse state when no persisted value exists. */
  defaultCollapsed?: boolean;
  /** Optional tailwind classes for the outer card. */
  className?: string;
  /** Optional tailwind classes for the header (background, border). */
  headerClassName?: string;
  /** Optional content rendered IN PLACE of children when the section is
   *  collapsed (e.g. a one-line hint that nudges the user to expand it). */
  whenCollapsedHint?: ReactNode;
  children: ReactNode;
}

function loadPersisted(key: string | undefined, fallback: boolean): boolean {
  if (!key || typeof window === 'undefined') return fallback;
  try {
    const v = window.localStorage.getItem(`collapsible:${key}`);
    if (v === '1') return true;
    if (v === '0') return false;
    return fallback;
  } catch {
    return fallback;
  }
}

function savePersisted(key: string | undefined, collapsed: boolean): void {
  if (!key || typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(`collapsible:${key}`, collapsed ? '1' : '0');
  } catch { /* private mode */ }
}

export function CollapsibleSection({
  title, icon, badge,
  persistKey, defaultCollapsed = false,
  className = '',
  headerClassName = '',
  whenCollapsedHint,
  children,
}: Props): JSX.Element {
  // Hydrate AFTER mount so SSR matches the initial collapsed=defaultCollapsed
  // render (avoids React hydration mismatch).
  const [collapsed, setCollapsed] = useState<boolean>(defaultCollapsed);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setCollapsed(loadPersisted(persistKey, defaultCollapsed));
    setHydrated(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [persistKey]);

  const toggle = useCallback(() => {
    setCollapsed(prev => {
      const next = !prev;
      savePersisted(persistKey, next);
      return next;
    });
  }, [persistKey]);

  return (
    <div className={className}>
      <button
        type="button"
        onClick={toggle}
        aria-expanded={collapsed ? 'false' : 'true'}
        className={`w-full flex items-center gap-2 text-left ${headerClassName}`}
      >
        {icon}
        <span className="flex-1 font-semibold text-gray-900">{title}</span>
        {badge && <span className="text-xs text-gray-600">{badge}</span>}
        {collapsed
          ? <ChevronDown className="h-4 w-4 text-gray-600 flex-shrink-0" aria-hidden="true" />
          : <ChevronUp   className="h-4 w-4 text-gray-600 flex-shrink-0" aria-hidden="true" />}
      </button>
      {hydrated && !collapsed && children}
      {hydrated && collapsed && whenCollapsedHint}
    </div>
  );
}
