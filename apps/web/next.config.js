/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: [
      "lucide-react",
      "@radix-ui/react-select",
      "@radix-ui/react-dialog",
    ],
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "assets.tcgdex.net",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "r2.limitlesstcg.net",
        pathname: "/pokemon/**",
      },
    ],
  },
  async headers() {
    const securityHeaders = [
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "X-Frame-Options", value: "DENY" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      {
        key: "Content-Security-Policy",
        value: [
          "default-src 'self'",
          "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
          "style-src 'self' 'unsafe-inline'",
          "img-src 'self' https://assets.tcgdex.net https://lh3.googleusercontent.com https://r2.limitlesstcg.net data:",
          "font-src 'self'",
          "connect-src 'self' https://api.trainerlab.io",
          "frame-ancestors 'none'",
        ].join("; "),
      },
      {
        key: "Permissions-Policy",
        value: "camera=(), microphone=(), geolocation=()",
      },
    ];

    if (process.env.NODE_ENV === "production") {
      securityHeaders.push({
        key: "Strict-Transport-Security",
        value: "max-age=31536000; includeSubDomains",
      });
    }

    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
};

module.exports = nextConfig;
