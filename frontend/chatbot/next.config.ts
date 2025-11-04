import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: 'standalone',
  
  // Environment-specific configuration
  env: {
    // Backend URL configuration for both client and server side
    BACKEND_URL: process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:5000',
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:5000',
    
    // App configuration
    NEXT_PUBLIC_APP_ENV: process.env.NEXT_PUBLIC_APP_ENV || process.env.NODE_ENV || 'development',
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'Edify AI Assistant',
    NEXT_PUBLIC_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION || '2.0.0',
  },
  
  // Environment variables exposed to the browser
  publicRuntimeConfig: {
    backendUrl: process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:5000',
    appEnv: process.env.NEXT_PUBLIC_APP_ENV || process.env.NODE_ENV || 'development',
    enableReasoning: process.env.NEXT_PUBLIC_ENABLE_REASONING === 'true',
    enableSources: process.env.NEXT_PUBLIC_ENABLE_SOURCES === 'true',
    enableVideos: process.env.NEXT_PUBLIC_ENABLE_VIDEOS === 'true',
    defaultRole: process.env.NEXT_PUBLIC_DEFAULT_ROLE || 'user',
    defaultNamespaces: process.env.NEXT_PUBLIC_DEFAULT_NAMESPACES || 'kb-psp,kb-msp',
    showNamespaceSelector: process.env.NEXT_PUBLIC_SHOW_NAMESPACE_SELECTOR === 'true',
    showRoleSelector: process.env.NEXT_PUBLIC_SHOW_ROLE_SELECTOR === 'true',
    enableStreaming: process.env.NEXT_PUBLIC_ENABLE_STREAMING !== 'false',
    streamDelayMs: parseInt(process.env.NEXT_PUBLIC_STREAM_DELAY_MS || '20'),
    apiTimeout: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000'),
    devMode: process.env.NEXT_PUBLIC_DEV_MODE === 'true',
    debugLogging: process.env.NEXT_PUBLIC_DEBUG_LOGGING === 'true',
  },
  
  // For production deployment
  trailingSlash: false,
  
  // Disable x-powered-by header for security
  poweredByHeader: false,
  
  // Compression for better performance
  compress: true,
  
  // Asset optimization
  images: {
    unoptimized: true, // Disable Next.js image optimization for static export
  },
  
  // Headers for security and CORS
  async headers() {
    return [
      {
        // Apply security headers to all routes
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
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
      {
        // Apply CORS headers to API routes
        source: '/api/(.*)',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: process.env.ALLOWED_ORIGINS || '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization',
          },
        ],
      },
    ];
  },
  
  // Webpack configuration for better builds
  webpack: (config, { isServer, dev }) => {
    // Optimize bundle size
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    
    // Development optimizations
    if (dev) {
      config.devtool = 'cheap-module-source-map';
    }
    
    return config;
  },
  
  // Experimental features
  experimental: {
    // Enable server components for better performance
    serverComponentsExternalPackages: [],
  },
};

export default nextConfig;
