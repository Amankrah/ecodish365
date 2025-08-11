import React from 'react';

export const Progress = ({ value = 0, className = '', ...props }) => {
  const clampedValue = Math.min(100, Math.max(0, value));

  return (
    <div
      className={`w-full bg-gray-200 rounded-full overflow-hidden ${className}`}
      {...props}
    >
      <div
        className="h-full bg-blue-600 transition-all duration-300 ease-in-out"
        style={{ width: `${clampedValue}%` }}
      />
    </div>
  );
};