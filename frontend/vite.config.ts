import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Igual que el rewrite de Vercel en producción: /api va al backend en el mismo dominio
    proxy: { '/api': 'http://localhost:8000' },
  },
})
