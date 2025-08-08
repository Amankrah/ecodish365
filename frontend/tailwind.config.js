/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // EcoDish365 Brand Colors - Professional Nutrition Platform
        primary: {
          50: '#ecfdf5',   // Very light green for backgrounds
          100: '#d1fae5',  // Light green for highlights
          200: '#a7f3d0',  // Soft green for accents
          300: '#6ee7b7',  // Medium green for interactive elements
          400: '#34d399',  // Bright green for primary actions
          500: '#10b981',  // Main brand green - nutrition & health
          600: '#059669',  // Dark green for hover states
          700: '#047857',  // Deeper green for emphasis
          800: '#065f46',  // Dark green for text
          900: '#064e3b',  // Very dark green
          950: '#022c22',  // Almost black green
        },
        secondary: {
          50: '#f0f9ff',   // Very light blue for backgrounds
          100: '#e0f2fe',  // Light blue for highlights
          200: '#bae6fd',  // Soft blue for accents
          300: '#7dd3fc',  // Medium blue for interactive elements
          400: '#38bdf8',  // Bright blue for secondary actions
          500: '#0ea5e9',  // Main brand blue - technology & analysis
          600: '#0284c7',  // Dark blue for hover states
          700: '#0369a1',  // Deeper blue for emphasis
          800: '#075985',  // Dark blue for text
          900: '#0c4a6e',  // Very dark blue
          950: '#082f49',  // Almost black blue
        },
        accent: {
          50: '#fef7ee',   // Very light orange for backgrounds
          100: '#fdedd3',  // Light orange for highlights
          200: '#fed7aa',  // Soft orange for accents
          300: '#fdba74',  // Medium orange for interactive elements
          400: '#fb923c',  // Bright orange for accent actions
          500: '#f97316',  // Main accent orange - energy & vitality
          600: '#ea580c',  // Dark orange for hover states
          700: '#c2410c',  // Deeper orange for emphasis
          800: '#9a3412',  // Dark orange for text
          900: '#7c2d12',  // Very dark orange
          950: '#431407',  // Almost black orange
        },
        // Semantic colors for nutrition data
        nutrition: {
          protein: '#ef4444',    // Red for protein
          carbs: '#f59e0b',      // Amber for carbohydrates
          fat: '#8b5cf6',        // Purple for fats
          fiber: '#22c55e',      // Green for fiber
          vitamin: '#3b82f6',    // Blue for vitamins
          mineral: '#6b7280',    // Gray for minerals
          energy: '#f97316',     // Orange for calories/energy
        },
        // Rating colors for HSR and FCS scores
        rating: {
          excellent: '#22c55e',  // Green for excellent scores (4.5-5 stars)
          good: '#84cc16',       // Light green for good scores (3.5-4 stars)
          average: '#eab308',    // Yellow for average scores (2.5-3 stars)
          poor: '#f97316',       // Orange for poor scores (1.5-2 stars)
          very_poor: '#ef4444',  // Red for very poor scores (0.5-1 stars)
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
} 