import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // In production (Docker/HF) the built files are served by FastAPI
  // at the same origin, so no proxy is needed.
  // In local dev, proxy /api to the FastAPI dev server.
  server: {
    port: 5173,
    proxy: {
      '/api':    { target: 'http://localhost:8000', changeOrigin: true },
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
