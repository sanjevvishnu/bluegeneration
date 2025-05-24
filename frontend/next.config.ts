import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Only enable static export for production
  ...(process.env.NODE_ENV === 'production' && {
    output: 'export',
    trailingSlash: true,
    images: {
      unoptimized: true
    }
  }),
  
  // Development configuration
  ...(process.env.NODE_ENV === 'development' && {
    images: {
      unoptimized: true
    }
  })
};

export default nextConfig;
