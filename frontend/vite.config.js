import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy API requests to the Flask backend during development.
    // This avoids CORS issues: the browser thinks it's talking to
    // localhost:5173, but Vite forwards /api/* and /socket.io/* to Flask.
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        ws: true,  // Enable WebSocket proxying
      },
    },
  },
})
