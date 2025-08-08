import React from 'react';
import { StarIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

interface StarRatingProps {
  rating: number;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showRating?: boolean;
  className?: string;
}

export default function StarRating({ 
  rating, 
  size = 'md', 
  showRating = false, 
  className = '' 
}: StarRatingProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
    xl: 'w-8 h-8'
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-lg',
    lg: 'text-xl',
    xl: 'text-2xl'
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 4.5) return 'text-green-500';
    if (rating >= 3.5) return 'text-green-400';
    if (rating >= 2.5) return 'text-yellow-400';
    if (rating >= 1.5) return 'text-orange-400';
    return 'text-red-400';
  };

  const renderStar = (index: number) => {
    const fillPercentage = Math.max(0, Math.min(1, rating - index));

    if (fillPercentage === 0) {
      // Empty star
      return (
        <StarIcon
          key={index}
          className={`${sizeClasses[size]} text-gray-300`}
        />
      );
    } else if (fillPercentage === 1) {
      // Full star
      return (
        <StarIconSolid
          key={index}
          className={`${sizeClasses[size]} text-yellow-400`}
        />
      );
    } else {
      // Half star (or partial fill)
      return (
        <div key={index} className="relative inline-block">
          <StarIcon
            className={`${sizeClasses[size]} text-gray-300`}
          />
          <div 
            className="absolute top-0 left-0 overflow-hidden"
            style={{ width: `${fillPercentage * 100}%` }}
          >
            <StarIconSolid
              className={`${sizeClasses[size]} text-yellow-400`}
            />
          </div>
        </div>
      );
    }
  };

  return (
    <div className={`flex items-center ${className}`}>
      {showRating && (
        <span className={`font-bold mr-2 ${textSizeClasses[size]} ${getRatingColor(rating)}`}>
          {rating.toFixed(1)}
        </span>
      )}
      <div className="flex">
        {[...Array(5)].map((_, index) => renderStar(index))}
      </div>
    </div>
  );
}
