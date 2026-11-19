import { fileURLToPath } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

const packagedInterface = fileURLToPath(
  new URL('../src/quantum_calculator/interfaces/api/static', import.meta.url),
)
const benchOrigin = process.env.QCALC_BENCH_ORIGIN ?? 'http://127.0.0.1:8421'

export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  build: {
    outDir: process.env.QCALC_WEB_OUT_DIR ?? packagedInterface,
    emptyOutDir: true,
    target: 'es2022',
    sourcemap: false,
    assetsInlineLimit: 0,
  },
  server: {
    host: '127.0.0.1',
    proxy: {
      '/api': { target: benchOrigin, changeOrigin: true, headers: { origin: benchOrigin } },
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
})
