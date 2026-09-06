import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'fs';
import path from 'path';

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
        changeOrigin: true,
        bypass(req) {
          const publicFile = path.resolve(__dirname, 'public', req.url.replace(/^\//, '').split('?')[0]);
          if (fs.existsSync(publicFile)) {
            return false;
          }
        }
      },
      '/samples': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        bypass(req) {
          const publicFile = path.resolve(__dirname, 'public', req.url.replace(/^\//, '').split('?')[0]);
          if (fs.existsSync(publicFile)) {
            return false;
          }
        }
      },
      '/recordings': {
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
