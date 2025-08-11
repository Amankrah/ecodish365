import React from 'react';

const badgeVariants = {
  default: 'bg-blue-100 text-blue-800',
  secondary: 'bg-gray-100 text-gray-800',
  destructive: 'bg-red-100 text-red-800',
  outline: 'bg-transparent text-gray-700 border border-gray-300'
};

export const Badge = ({ variant = 'default', className = '', children, ...props }) => {
  const baseClasses = 'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium';
  const variantClasses = badgeVariants[variant] || badgeVariants.default;

  return (
    <span
      className={`${baseClasses} ${variantClasses} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};