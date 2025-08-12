'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import EcoDishLogo from './EcoDishLogo';
import { usePathname } from 'next/navigation';
import { 
  Bars3Icon, 
  XMarkIcon,
  ChartBarIcon,
  StarIcon,
  SparklesIcon,
  ScaleIcon,
  HeartIcon,
  ChevronDownIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

const navigation = [
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
    name: 'HSR', 
    href: '/hsr', 
    icon: StarIcon,
    dropdown: [
      { name: 'Calculate HSR', href: '/hsr/calculate' },
      { name: 'Compare Foods', href: '/hsr/compare' },
      { name: 'Food Profile', href: '/hsr/food-profile' },
      { name: 'Meal Insights', href: '/hsr/meal-insights' },
    ]
  },
  { 
    name: 'FCS', 
    href: '/fcs', 
    icon: SparklesIcon,
    dropdown: [
      { name: 'Calculate FCS', href: '/fcs/calculate' },
      { name: 'Compare Foods', href: '/fcs/compare' },
      { name: 'Food Profile', href: '/fcs/food-profile' },
    ]
  },
  { 
    name: 'HEFI', 
    href: '/hefi', 
    icon: ScaleIcon,
    dropdown: [
      { name: 'Calculate HEFI', href: '/hefi/calculate' },
      { name: 'Compare Foods', href: '/hefi/compare' },
      { name: 'Food Profile', href: '/hefi/food-profile' },
    ]
  },
  { 
    name: 'HENI', 
    href: '/heni', 
    icon: HeartIcon,
    dropdown: [
      { name: 'Individual Calculator', href: '/heni/calculate' },
      { name: 'Policy Dashboard', href: '/heni/policy-dashboard' },
    ]
  },
  { 
    name: 'Environmental Impact', 
    href: '/environmental', 
    icon: GlobeAltIcon,
    dropdown: [
      { name: 'Calculate Impact', href: '/environmental/calculate' },
      { name: 'Compare Foods', href: '/environmental/compare' },
    ]
  },
  
];

export default function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const pathname = usePathname();

  return (
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
            {navigation.map((item) => {
              const isActive = pathname === item.href || 
                (item.href !== '/' && pathname.startsWith(item.href));
              const isDropdownOpen = activeDropdown === item.name;
              
              return (
                <div key={item.name} className="relative group">
                  <div
                    onMouseEnter={() => setActiveDropdown(item.name)}
                    className={clsx(
                      'flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 relative group',
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
                    <button
                      type="button"
                      onClick={() => setActiveDropdown(isDropdownOpen ? null : item.name)}
                      className="p-1"
                      aria-label={`Toggle ${item.name} dropdown`}
                    >
                      <ChevronDownIcon className={clsx(
                        'w-4 h-4 transition-transform duration-200',
                        isDropdownOpen ? 'rotate-180' : '',
                        isActive ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'
                      )} />
                    </button>
                  </div>
                  
                  {/* Dropdown Menu */}
                  {isDropdownOpen && (
                    <div 
                      className="absolute top-full left-0 mt-2 w-56 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 py-2 z-50"
                      onMouseLeave={() => setActiveDropdown(null)}
                    >
                      {item.dropdown?.map((dropdownItem) => {
                        const isDropdownActive = pathname === dropdownItem.href;
                        return (
                          <Link
                            key={dropdownItem.href}
                            href={dropdownItem.href}
                            className={clsx(
                              'block px-4 py-2 text-sm transition-all duration-200 mx-2 rounded-lg',
                              isDropdownActive
                                ? 'bg-gradient-to-r from-blue-50 to-green-50 text-blue-700 font-medium'
                                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50/80'
                            )}
                            onClick={() => setActiveDropdown(null)}
                          >
                            {dropdownItem.name}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
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
            {navigation.map((item) => {
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
                  
                  {/* Dropdown Items */}
                  <div className="ml-4 space-y-1">
                    {item.dropdown?.map((dropdownItem) => {
                      const isDropdownActive = pathname === dropdownItem.href;
                      return (
                        <Link
                          key={dropdownItem.href}
                          href={dropdownItem.href}
                          onClick={() => setMobileMenuOpen(false)}
                          className={clsx(
                            'block px-4 py-2 text-sm rounded-lg transition-all duration-200',
                            isDropdownActive
                              ? 'bg-gradient-to-r from-blue-50 to-green-50 text-blue-700 font-medium border border-blue-100'
                              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50/80'
                          )}
                        >
                          {dropdownItem.name}
                        </Link>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </nav>
  );
} 