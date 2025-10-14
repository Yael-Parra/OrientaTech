import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Dev server proxy to forward API requests to the backend and avoid CORS in development
  server: {
    proxy: {
      // Proxy calls starting with /auth to the FastAPI backend
      '/auth': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/auth/, '/auth'),
      },
      // Proxy calls starting with /profile to the FastAPI backend
      '/profile': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/profile/, '/profile'),
      },
      // Proxy calls starting with /documents to the FastAPI backend
      '/documents': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/documents/, '/documents'),
      },
      // Proxy calls starting with /api to the FastAPI backend (includes RAG endpoints)
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
  },
})
