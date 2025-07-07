import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Output configuration for production deployment
  output: 'standalone',
  
  // Enable static optimization
  trailingSlash: false,
  
  // Image optimization
  images: {
    unoptimized: true, // Disable for static export compatibility
  },
  
  // Performance optimizations
  poweredByHeader: false,
  
  // Compression
  compress: true,
  
  // API routes configuration
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
  
  // Environment variables that should be available to the client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT,
    NEXT_PUBLIC_DOMAIN: process.env.NEXT_PUBLIC_DOMAIN,
    NEXT_PUBLIC_PROTOCOL: process.env.NEXT_PUBLIC_PROTOCOL,
  },
  
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },
}

export default nextConfig;
