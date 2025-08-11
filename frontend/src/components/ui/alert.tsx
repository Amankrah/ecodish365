import React from 'react';

type DivProps = React.HTMLAttributes<HTMLDivElement>;

export const Alert = ({ className = '', children, ...props }: DivProps) => {
  return (
    <div className={`p-4 rounded-lg border ${className}`} {...props}>
      {children}
    </div>
  );
};

export const AlertDescription = ({ className = '', children, ...props }: DivProps) => {
  return (
    <div className={`text-sm ${className}`} {...props}>
      {children}
    </div>
  );
};