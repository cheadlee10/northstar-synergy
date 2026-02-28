import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    strictPort: false,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'recharts': ['recharts'],
          'ant-charts': ['@ant-design/charts'],
        }
      }
    }
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'recharts', '@ant-design/charts']
  }
});
