import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === "production";
// Set basePath for GitHub Pages project site (https://<username>.github.io/<repo>/)
const repoName = "/Paper-2-Project";
const basePath = isProd ? repoName : "";

const nextConfig: NextConfig = {
  output: "export",
  basePath: basePath,
  env: {
    NEXT_PUBLIC_BASE_PATH: basePath,
  },
  images: {
    unoptimized: true,
  },
  // Ensure trailing slashes for GitHub Pages static directory serving
  trailingSlash: true,
};

export default nextConfig;
