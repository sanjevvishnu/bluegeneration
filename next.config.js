/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow loading prompts.json as a static file
  async rewrites() {
    return [
      {
        source: '/api/prompts',
        destination: '/prompts.json',
      },
    ];
  },
}

module.exports = nextConfig 