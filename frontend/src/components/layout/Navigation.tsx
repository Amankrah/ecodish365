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
  UserIcon,
  PlusCircleIcon,
  BookmarkIcon,
  ClockIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

type DropdownChild = { name: string; href: string };
type DropdownItem = { name: string; href: string; children?: DropdownChild[] };
type NavItem = {
  name: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  requiresAuth?: boolean;
  dropdown?: DropdownItem[];
};

const navigation: NavItem[] = [
  { 
    name: 'CNF Explorer', 
    href: '/cnf', 
    icon: ChartBarIcon,
    dropdown: [
      { name: 'Food Search', href: '/cnf/search' },
      { name: 'Compare Foods', href: '/cnf/compare' },
      { name: 'Food Groups', href: '/cnf/groups' },
      { name: 'Analytics', href: '/cnf/analytics' },
    ]
  },
  { 
    name: 'Nutrition Indicators', 
    href: '/hsr', 
    icon: ScaleIcon,
    dropdown: [
      { 
        name: 'HSR', 
        href: '/hsr', 
        children: [
          { name: 'Calculate HSR', href: '/hsr/calculate' },
          { name: 'Compare Foods', href: '/hsr/compare' },
          { name: 'Food Profile', href: '/hsr/food-profile' },
          { name: 'Meal Insights', href: '/hsr/meal-insights' },
        ]
      },
      { 
        name: 'FCS', 
        href: '/fcs', 
        children: [
          { name: 'Calculate FCS', href: '/fcs/calculate' },
          { name: 'Compare Foods', href: '/fcs/compare' },
          { name: 'Food Profile', href: '/fcs/food-profile' },
        ]
      },
      { 
        name: 'HEFI', 
        href: '/hefi', 
        children: [
          { name: 'Calculate HEFI', href: '/hefi/calculate' },
          { name: 'Compare Foods', href: '/hefi/compare' },
          { name: 'Food Profile', href: '/hefi/food-profile' },
        ]
      },
      { 
        name: 'HENI', 
        href: '/heni', 
        children: [
          { name: 'Individual Calculator', href: '/heni/calculate' },
          { name: 'Policy Dashboard', href: '/heni/policy-dashboard' },
        ]
      },
    ]
  },
  {
    name: 'Environmental Indicators',
    href: '/environmental',
    icon: GlobeAltIcon,
    dropdown: [
      { name: 'Calculate Impact', href: '/environmental/calculate' },
      { name: 'Compare Foods', href: '/environmental/compare' },
    ]
  },
  // RECALL-HISTORY-1 (2026-05-24): surface the 24-h recall → history →
  // dietary-pattern workflow in the top nav so users (especially returning
  // users with saved days) can find their browser-local history without
  // having to remember the /recall-history URL.
  {
    name: 'Dietary Recall',
    href: '/recall-24h',
    icon: ClockIcon,
    dropdown: [
      { name: 'Log a 24-h recall', href: '/recall-24h' },
      { name: 'My recall history', href: '/recall-history' },
      { name: 'Dietary pattern', href: '/dietary-pattern' },
      // PKG-IMG-1 Phase 1 (2026-05-26): camera-based input for users
      // who want to score a single packaged product without going
      // through the full recall wizard.
      { name: 'Scan packaged food', href: '/scan-product' },
    ],
  },
  {
    name: 'Meals',
    href: '/meals', 
    icon: PlusCircleIcon,
    requiresAuth: true,
    dropdown: [
      { name: 'Create Meal', href: '/meals/create' },
      { name: 'My Meals', href: '/meals/my-meals' },
      { name: 'Saved Meals', href: '/meals/saved-meals' },
      { name: 'Discover Meals', href: '/meals' },
    ]
  },
];

export default function Navigation() {
  const { isAuthenticated, user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
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

  // Compute contextual sub-navigation for current section
  const getContextSubnav = (): DropdownChild[] => {
    const currentPath = pathname || '/';
    // Nutrition Indicators context (HSR/FCS/HEFI/HENI)
    const nutrition = filteredNavigation.find((n) => n.name === 'Nutrition Indicators');
    if (nutrition?.dropdown && Array.isArray(nutrition.dropdown)) {
      const match = nutrition.dropdown.find((d) => currentPath.startsWith(d.href));
      if (match?.children && match.children.length > 0) {
        return match.children;
      }
    }

    // Environmental Indicators context
    const environmental = filteredNavigation.find((n) => n.name === 'Environmental Indicators');
    if (environmental?.dropdown && currentPath.startsWith(environmental.href)) {
      return environmental.dropdown.map((d) => ({ name: d.name, href: d.href }));
    }

    return [];
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
              const showDropdown = Array.isArray(item.dropdown) && (
                item.name === 'CNF Explorer' || item.name === 'Environmental Indicators' || item.name === 'Nutrition Indicators' || item.name === 'Meals' || item.name === 'Dietary Recall'
              );
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
                      className="absolute top-full left-0 mt-2 w-64 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 py-2 z-50"
                      onMouseEnter={() => openDropdown(item.name)}
                      onMouseLeave={scheduleCloseDropdown}
                    >
                      {item.dropdown?.map((d: DropdownItem) => {
                        // For Nutrition Indicators, only show main paths (no children)
                        if (item.name === 'Nutrition Indicators') {
                          return (
                            <Link
                              key={d.href}
                              href={d.href}
                              className={clsx('block px-4 py-2 text-sm mx-2 rounded-lg transition-colors',
                                pathname.startsWith(d.href)
                                  ? 'bg-gradient-to-r from-blue-50 to-green-50 text-blue-700'
                                  : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50/80'
                              )}
                            >
                              {d.name}
                            </Link>
                          );
                        }
                        // For CNF/Environmental, show their subdirectories
                        return (
                          <Link
                            key={d.href}
                            href={d.href}
                            className={clsx('block px-4 py-2 text-sm mx-2 rounded-lg transition-colors',
                              pathname === d.href
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
            
            {/* User Menu / Auth Buttons */}
            <div className="flex items-center space-x-3 ml-4 pl-4 border-l border-gray-200">
              {isAuthenticated ? (
                <div className="relative">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center space-x-2 p-2 rounded-xl text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50/80 transition-all duration-200"
                  >
                    <div className="w-8 h-8 bg-gradient-primary rounded-full flex items-center justify-center">
                      <span className="text-white text-sm font-semibold">
                        {user?.first_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
                      </span>
                    </div>
                    <ChevronDownIcon className={clsx(
                      'w-4 h-4 transition-transform duration-200',
                      userMenuOpen ? 'rotate-180' : ''
                    )} />
                  </button>
                  
                  {userMenuOpen && (
                    <div className="absolute right-0 top-full mt-2 w-56 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 py-2 z-50">
                      <div className="px-4 py-2 border-b border-gray-200">
                        <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                        <p className="text-xs text-gray-500">{user?.email}</p>
                      </div>
                      <Link
                        href="/meals/create"
                        className="flex items-center px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50/80 mx-2 rounded-lg transition-all duration-200"
                        onClick={() => setUserMenuOpen(false)}
                      >
                        <PlusCircleIcon className="w-4 h-4 mr-3" />
                        Create Meal
                      </Link>
                      <Link
                        href="/meals/my-meals"
                        className="flex items-center px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50/80 mx-2 rounded-lg transition-all duration-200"
                        onClick={() => setUserMenuOpen(false)}
                      >
                        <BookmarkIcon className="w-4 h-4 mr-3" />
                        My Meals
                      </Link>
                      <Link
                        href="/recall-history"
                        className="flex items-center px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50/80 mx-2 rounded-lg transition-all duration-200"
                        onClick={() => setUserMenuOpen(false)}
                      >
                        <ClockIcon className="w-4 h-4 mr-3" />
                        My recall history
                      </Link>
                      <Link
                        href="/profile"
                        className="flex items-center px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50/80 mx-2 rounded-lg transition-all duration-200"
                        onClick={() => setUserMenuOpen(false)}
                      >
                        <UserIcon className="w-4 h-4 mr-3" />
                        Profile Settings
                      </Link>
                      <hr className="my-2 border-gray-200" />
                      <button
                        onClick={() => {
                          logout();
                          setUserMenuOpen(false);
                        }}
                        className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50/80 mx-2 rounded-lg transition-all duration-200"
                      >
                        <ArrowRightOnRectangleIcon className="w-4 h-4 mr-3" />
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Link
                    href="/auth/login"
                    className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50/80 rounded-xl transition-all duration-200"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/auth/register"
                    className="px-3 py-2 text-sm font-medium text-white bg-gradient-primary hover:opacity-90 rounded-xl transition-all duration-200"
                  >
                    Sign Up
                  </Link>
                </div>
              )}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-gray-600 hover:text-gray-900 hover:bg-gray-100/80 transition-all duration-200"
            >
              {mobileMenuOpen ? (
                <XMarkIcon className="w-6 h-6" />
              ) : (
                <Bars3Icon className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden">
          <div className="px-4 pt-2 pb-4 space-y-2 bg-white/95 backdrop-blur-sm border-t border-gray-200/50">
            {filteredNavigation.map((item) => {
              const isActive = pathname === item.href || 
                (item.href !== '/' && pathname.startsWith(item.href));
              
              return (
                <div key={item.name} className="space-y-1">
                  {/* Main Category */}
                  <div className={clsx(
                    'flex items-center space-x-3 px-4 py-3 rounded-xl text-base font-medium',
                    isActive
                      ? 'bg-gradient-to-r from-blue-50 to-green-50 text-blue-700 shadow-sm border border-blue-100'
                      : 'text-gray-700'
                  )}>
                    <item.icon className={clsx(
                      'w-5 h-5',
                      isActive ? 'text-blue-600' : 'text-gray-500'
                    )} />
                    <span>{item.name}</span>
                  </div>
                  
          {/* No dropdown items on mobile; use context sub-nav below */}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </nav>
    {/* Contextual Sub-Navigation Bar */}
    {contextSubnav.length > 0 && (
      <div className="bg-white/95 backdrop-blur-sm border-b border-gray-200/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 overflow-x-auto py-2">
            {contextSubnav.map((link) => {
              const active = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href));
              return (
                <Link
                  key={link.href}
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