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
      sourcemap: isDev,
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
          // Ensure CSS is inlined in the JS bundle
          inlineDynamicImports: true,
        },
      },
      ...(!isDev && {
        esbuild: {
          drop: ["console", "debugger"],
          minifyIdentifiers: true,
          minifySyntax: true,
          minifyWhitespace: true,
        },
      }),
    },
  } satisfies UserConfig;
});
