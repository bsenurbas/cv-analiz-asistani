import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Tarayıcıdan '/api' ile başlayan bir istek gittiğinde Vite bunu yakalar
      // ve arka planda localhost:8000'e (FastAPI) yönlendirir.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // Backend'de rotalarınız zaten '/api/cv/analyze' gibi '/api' ile başladığı için
        // herhangi bir path rewrite (yol sıfırlama) işlemine gerek yoktur.
      }
    }
  }
})