import react from "@vitejs/plugin-react";
import process from "node:process";
import { defineConfig, UserConfig } from "vite";

/**
 * Vite configuration for Streamlit AgGrid Component v2 development using React.
 *
 * @see https://vitejs.dev/config/ for complete Vite configuration options.
 */
export default defineConfig(() => {
  const isProd = process.env.NODE_ENV === "production";
  const isDev = !isProd;

  return {
    base: "./",
    plugins: [react()],
    publicDir: "public",
    define: {
      // We are building in library mode, we need to define the NODE_ENV
      // variable to prevent issues when executing the JS.
      "process.env.NODE_ENV": JSON.stringify(process.env.NODE_ENV),
    },
    build: {
      minify: isDev ? false : "esbuild",
      outDir: "build",
      // Always generate source maps for debugging (use 'hidden' in prod to not expose in browser)
      sourcemap: isDev ? true : "hidden",
      // Inline CSS into the JS bundle for Streamlit components
      cssCodeSplit: false,
      // Enable watch mode for development
      watch: isDev ? {} : null,
      lib: {
        entry: "./src/index.tsx",
        name: "AgGridComponent",
        formats: ["es"],
        fileName: "index-[hash]",
      },
      rollupOptions: {
        output: {
          // Streamlit serves component assets with public caching. Give the
          // single emitted stylesheet a real content hash so upgrades cannot
          // reuse stale CSS through a browser or reverse proxy cache.
          assetFileNames: "index-[hash][extname]",
          inlineDynamicImports: true,
        },
      },
      ...(!isDev && {
        esbuild: {
          // Keep warnings and errors: row-ID contract failures and collector
          // errors must remain diagnosable in the published component.
          drop: ["debugger"],
          pure: ["console.log", "console.debug"],
          minifyIdentifiers: true,
          minifySyntax: true,
          minifyWhitespace: true,
        },
      }),
    },
  } satisfies UserConfig;
});
