import React from 'react';
import type { ProgressHTMLAttributes } from 'react';

interface ProgressProps extends ProgressHTMLAttributes<HTMLProgressElement> {
  value?: number;
}

export const Progress: React.FC<ProgressProps> = ({ value = 0, className = '', ...props }) => {
  const clampedValue = Math.min(100, Math.max(0, value));

  return (
    <progress
      value={clampedValue}
      max={100}
      className={`w-full h-2 ${className}`}
      {...props}
    />
  );
};