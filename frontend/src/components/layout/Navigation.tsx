'use client';

import React, { useState, useRef } from 'react';
import Link from 'next/link';
import EcoDishLogo from './EcoDishLogo';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  Bars3Icon,
  XMarkIcon,
  ChartBarIcon,
  ScaleIcon,
  ChevronDownIcon,
  GlobeAltIcon,
  ClockIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { CATALOGUE_DROPDOWN, CATALOGUE_NAV } from '@/lib/catalogueNav';
import { RESEARCH_DROPDOWN, RESEARCH_NAV } from '@/lib/researchNav';

type DropdownChild = {
  name: string;
  href: string;
  disabled?: boolean;
};
type NavItem = {
  name: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  requiresAuth?: boolean;
  dropdown: readonly DropdownChild[];
};

// Top-level navigation: functional categories with each individual metric
// surfaced directly in its dropdown so researchers can run any single
// lens calculator in one click. Per-lens overview pages (/hefi, /heni,
// /hsr, /fcs, /environmental) remain reachable via the contextual
// sub-nav once you are on a lens path.
const navigation: NavItem[] = [
  {
    name: CATALOGUE_NAV.section,
    href: CATALOGUE_NAV.href,
    icon: ChartBarIcon,
    dropdown: CATALOGUE_DROPDOWN,
  },
  // PLATFORM-CODE-1.l (2026-06-26): top-level Research category. The hub
  // and its researcher-facing surfaces (Nutrient analysis, Cohort upload,
  // Compare cohorts) used to be tucked under Food Catalogue, which meant
  // a returning researcher had no way to land on /research without
  // remembering the URL. Promoted to its own dropdown.
  {
    name: RESEARCH_NAV.section,
    href: RESEARCH_NAV.href,
    icon: BeakerIcon,
    dropdown: RESEARCH_DROPDOWN,
  },
  {
    name: 'Nutrition Indicators',
    href: '/scorecard',
    icon: ScaleIcon,
    // Top-line entries only — one per lens, going straight to its
    // calculator. Compare / overview pages reachable via the contextual
    // sub-nav once on a lens path, so we do not duplicate them here.
    dropdown: [
      { name: 'All scores at once', href: '/scorecard' },
      { name: 'HEFI', href: '/hefi/calculate' },
      { name: 'HENI', href: '/heni/calculate' },
      { name: 'HSR', href: '/hsr/calculate' },
      { name: 'Food Compass', href: '/fcs/calculate' },
      { name: 'Scan packaged food', href: '/scan-product' },
      { name: 'Improve one meal', href: '/improve-product' },
    ],
  },
  {
    name: 'Environmental Indicators',
    href: '/environmental',
    icon: GlobeAltIcon,
    dropdown: [
      { name: 'Environmental impact', href: '/environmental/calculate' },
      // PLANETARY-1 (2026-05-27): EAT-Lancet 2.0 Table 2 food-system share.
      { name: 'Planet budget share', href: '/planetary' },
    ],
  },
  // RECALL-HISTORY-1 (2026-05-24): surface the 24-h recall → history →
  // dietary-pattern workflow in the top nav so users (especially returning
  // users with saved days) can find their browser-local history without
  // having to remember the /recall-history URL.
  {
    name: 'Food diary',
    href: '/recall-24h',
    icon: ClockIcon,
    dropdown: [
      { name: 'Log a day', href: '/recall-24h' },
      { name: 'Saved days', href: '/recall-history' },
      { name: 'Analyze days', href: '/recall-history/analyze' },
      { name: 'Dietary pattern', href: '/dietary-pattern' },
    ],
  },
];

// Path-to-category routing for the contextual sub-nav bar. First match
// wins. Routes /research/* to the Research dropdown (PLATFORM-CODE-1.l)
// so the sub-nav strip on Nutrient analysis / Cohort upload shows the
// research-specific tabs rather than the catalogue tabs.
const CATEGORY_ROUTES: Array<{ prefix: string; category: string }> = [
  { prefix: '/cnf', category: CATALOGUE_NAV.section },
  { prefix: '/research', category: RESEARCH_NAV.section },
  { prefix: '/scorecard', category: 'Nutrition Indicators' },
  { prefix: '/hefi', category: 'Nutrition Indicators' },
  { prefix: '/heni', category: 'Nutrition Indicators' },
  { prefix: '/hsr', category: 'Nutrition Indicators' },
  { prefix: '/fcs', category: 'Nutrition Indicators' },
  { prefix: '/scan-product', category: 'Nutrition Indicators' },
  { prefix: '/improve-product', category: 'Nutrition Indicators' },
  { prefix: '/environmental', category: 'Environmental Indicators' },
  { prefix: '/planetary', category: 'Environmental Indicators' },
  { prefix: '/recall-24h', category: 'Food diary' },
  { prefix: '/recall-history', category: 'Food diary' },
  { prefix: '/dietary-pattern', category: 'Food diary' },
];

export default function Navigation() {
  const { isAuthenticated } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const closeTimeoutRef = useRef<number | null>(null);
  const pathname = usePathname();

  const openDropdown = (name: string) => {
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
    setActiveDropdown(name);
  };

  const scheduleCloseDropdown = () => {
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
    }
    closeTimeoutRef.current = window.setTimeout(() => {
      setActiveDropdown(null);
    }, 180);
  };

  const filteredNavigation = navigation.filter(item =>
    !item.requiresAuth || isAuthenticated
  );

  // Compute contextual sub-navigation for the current section.
  const getContextSubnav = (): DropdownChild[] => {
    const currentPath = pathname || '/';
    const match = CATEGORY_ROUTES.find((r) => currentPath.startsWith(r.prefix));
    if (!match) return [];
    const item = filteredNavigation.find((n) => n.name === match.category);
    if (!item) return [];
    return [...item.dropdown];
  };

  const contextSubnav = getContextSubnav();

  return (
    <>
    <nav className="bg-white/95 backdrop-blur-sm shadow-lg border-b border-gray-200/50 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center" aria-label="EcoDish365 Home">
              <EcoDishLogo variant="brand" className="w-10 h-10 hover:scale-105 transition-transform duration-200" />
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {filteredNavigation.map((item) => {
              const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
              const isDropdownOpen = activeDropdown === item.name;
              const showDropdown = Array.isArray(item.dropdown) && item.dropdown.length > 0;
              return (
                <div key={item.name} className="relative group">
                  <div
                    onMouseEnter={() => showDropdown && openDropdown(item.name)}
                    onMouseLeave={() => showDropdown && scheduleCloseDropdown()}
                    className={clsx(
                      'flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 relative',
                      isActive
                        ? 'bg-gradient-to-r from-blue-50 to-green-50 text-blue-700 shadow-sm border border-blue-100'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50/80'
                    )}
                  >
                    <item.icon className={clsx(
                      'w-4 h-4 transition-colors duration-200',
                      isActive ? 'text-blue-600' : 'text-gray-500 group-hover:text-gray-700'
                    )} />
                    <Link href={item.href} className="flex-1">
                      <span className="relative">
                        {item.name}
                        {isActive && (
                          <div className="absolute -bottom-1 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 to-green-500 rounded-full" />
                        )}
                      </span>
                    </Link>
                    {showDropdown && (
                      <button
                        type="button"
                        onClick={() => setActiveDropdown(isDropdownOpen ? null : item.name)}
                        aria-label={`Toggle ${item.name} menu`}
                        className="p-1 ml-1"
                      >
                        <ChevronDownIcon className={clsx(
                          'w-4 h-4 transition-transform duration-200',
                          isDropdownOpen ? 'rotate-180' : '',
                          isActive ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'
                        )} />
                      </button>
                    )}
                  </div>
                  {showDropdown && isDropdownOpen && (
                    <div
                      className="absolute top-full left-0 mt-2 w-72 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 py-2 z-50"
                      onMouseEnter={() => openDropdown(item.name)}
                      onMouseLeave={scheduleCloseDropdown}
                    >
                      {item.dropdown.map((d) => {
                        const active = pathname === d.href || (d.href !== '/' && pathname.startsWith(d.href.split('#')[0]));
                        if (d.disabled) {
                          return (
                            <div
                              key={d.href + d.name}
                              className="flex items-center justify-between px-4 py-2 text-sm mx-2 rounded-lg text-gray-400 cursor-not-allowed"
                              aria-disabled="true"
                            >
                              <span>{d.name}</span>
                              <span className="text-xs font-semibold uppercase tracking-wide bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded-full">Soon</span>
                            </div>
                          );
                        }
                        return (
                          <Link
                            key={d.href + d.name}
                            href={d.href}
                            className={clsx(
                              'block px-4 py-2 text-sm mx-2 rounded-lg transition-colors',
                              active
                                ? 'bg-gradient-to-r from-blue-50 to-green-50 text-blue-700'
                                : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50/80'
                            )}
                          >
                            {d.name}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}

            {/* Auth controls intentionally removed from the nav (2026-06-26).
                Login + registration + the user menu live at /auth/login,
                /auth/register, and /profile; routes still work, but the nav
                stays focused on platform surfaces (research, catalogue,
                indicators) rather than account management. */}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            {mobileMenuOpen ? (
              <button
                type="button"
                onClick={() => setMobileMenuOpen(false)}
                aria-label="Close menu"
                aria-expanded="true"
                aria-controls="mobile-nav-drawer"
                className="p-2 rounded-xl text-gray-600 hover:text-gray-900 hover:bg-gray-100/80 transition-all duration-200"
              >
                <XMarkIcon className="w-6 h-6" aria-hidden="true" />
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setMobileMenuOpen(true)}
                aria-label="Open menu"
                aria-expanded="false"
                aria-controls="mobile-nav-drawer"
                className="p-2 rounded-xl text-gray-600 hover:text-gray-900 hover:bg-gray-100/80 transition-all duration-200"
              >
                <Bars3Icon className="w-6 h-6" aria-hidden="true" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Navigation — always in DOM so aria-controls stays valid */}
      <div
        id="mobile-nav-drawer"
        className={clsx('md:hidden', !mobileMenuOpen && 'hidden')}
        hidden={!mobileMenuOpen}
      >
        {mobileMenuOpen && (
          <div className="px-4 pt-2 pb-4 space-y-2 bg-white/95 backdrop-blur-sm border-t border-gray-200/50">
            {filteredNavigation.map((item) => {
              const isActive = pathname === item.href ||
                (item.href !== '/' && pathname.startsWith(item.href));

              return (
                <div key={item.name} className="space-y-1">
                  <Link
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={clsx(
                      'flex items-center space-x-3 px-4 py-3 rounded-xl text-base font-medium',
                      isActive
                        ? 'bg-gradient-to-r from-blue-50 to-green-50 text-blue-700 shadow-sm border border-blue-100'
                        : 'text-gray-700 hover:bg-gray-50'
                    )}
                  >
                    <item.icon
                      className={clsx(
                        'w-5 h-5',
                        isActive ? 'text-blue-600' : 'text-gray-500'
                      )}
                      aria-hidden="true"
                    />
                    <span>{item.name}</span>
                  </Link>
                  {/* Stack each dropdown item beneath its category so mobile users
                      can reach lens calculators and other sub-pages directly. */}
                  {item.dropdown.length > 0 && (
                    <div className="pl-7 pr-2 space-y-0.5">
                      {item.dropdown.map((d) => {
                        if (d.disabled) {
                          return (
                            <div
                              key={d.href + d.name}
                              className="flex items-center justify-between px-3 py-2 text-sm rounded-lg text-gray-400 cursor-not-allowed"
                              aria-disabled="true"
                            >
                              <span>{d.name}</span>
                              <span className="text-xs font-semibold uppercase tracking-wide bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded-full">Soon</span>
                            </div>
                          );
                        }
                        const subActive = pathname === d.href || (d.href !== '/' && pathname.startsWith(d.href.split('#')[0]));
                        return (
                          <Link
                            key={d.href + d.name}
                            href={d.href}
                            onClick={() => setMobileMenuOpen(false)}
                            className={clsx(
                              'block px-3 py-2 text-sm rounded-lg transition-colors',
                              subActive
                                ? 'bg-blue-50 text-blue-700'
                                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                            )}
                          >
                            {d.name}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </nav>
    {/* Contextual Sub-Navigation Bar */}
    {contextSubnav.length > 0 && (
      <div className="bg-white/95 backdrop-blur-sm border-b border-gray-200/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 overflow-x-auto py-2">
            {contextSubnav.map((link) => {
              if (link.disabled) {
                return (
                  <span
                    key={link.href + link.name}
                    className="px-3 py-1.5 rounded-lg text-sm whitespace-nowrap text-gray-400 inline-flex items-center gap-1.5"
                    aria-disabled="true"
                  >
                    {link.name}
                    <span className="text-xs font-semibold uppercase tracking-wide bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded-full">Soon</span>
                  </span>
                );
              }
              const active = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href.split('#')[0]));
              return (
                <Link
                  key={link.href + link.name}
                  href={link.href}
                  className={clsx(
                    'px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-colors duration-200',
                    active
                      ? 'bg-gradient-to-r from-blue-50 to-green-50 text-blue-700 border border-blue-100'
                      : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                  )}
                >
                  {link.name}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    )}
    </>
  );
}
