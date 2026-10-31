import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Gera uma versão enxuta do site, pronta para rodar no Docker
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
  // Liga o Tailwind (sem isso o site fica sem estilo)
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;