import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/clips': {
        target: 'https://localhost:7061',
        changeOrigin: true,
        secure: false,
      },
      '/instagram': {
        target: 'https://localhost:7061',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
