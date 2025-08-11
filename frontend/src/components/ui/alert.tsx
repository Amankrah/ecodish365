import React from 'react';

export const Alert = ({ className = '', children, ...props }) => {
  return (
    <div
      className={`p-4 rounded-lg border ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const AlertDescription = ({ className = '', children, ...props }) => {
  return (
    <div
      className={`text-sm ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};