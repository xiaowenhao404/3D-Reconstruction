import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

// @mkkellogg/gaussian-splats-3d 内含 web worker + wasm，必须从依赖预打包中排除，
// 否则 Vite 的 optimizeDeps 会破坏其 worker 加载。
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  optimizeDeps: {
    exclude: ['@mkkellogg/gaussian-splats-3d'],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/static': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
});
