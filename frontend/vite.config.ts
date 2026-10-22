import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    // PWA solo para poder instalarla: el service worker no guarda nada en caché (sin modo sin conexión)
    VitePWA({
      registerType: 'autoUpdate',
      includeManifestIcons: false,
      manifest: {
        name: 'BODEGA · Inventario',
        short_name: 'BODEGA',
        description: 'Control de productos de la bodega: stock, valor, entradas y salidas',
        lang: 'es',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        background_color: '#f1f5f9',
        theme_color: '#047857',
        icons: [
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png' },
          { src: 'maskable-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        globPatterns: [],
        navigateFallback: null,
        runtimeCaching: [],
      },
    }),
  ],
  server: {
    // Igual que el rewrite de Vercel en producción: /api va al backend en el mismo dominio
    proxy: { '/api': 'http://localhost:8000' },
  },
})
