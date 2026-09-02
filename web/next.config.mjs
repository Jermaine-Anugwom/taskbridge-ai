const isPages = process.env.GITHUB_ACTIONS === "true";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  basePath: isPages ? "/taskbridge-ai" : "",
  assetPrefix: isPages ? "/taskbridge-ai/" : undefined,
};

export default nextConfig;
