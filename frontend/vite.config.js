import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  envDir: '../',
  server: {

    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/stream': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/snapshots': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/recordings': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/samples': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/evidence': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
