/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./App.jsx",
    "./components/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        northstar: {
          dark: '#1a1a2e',
          cyan: '#00d4ff',
          secondary: '#16213e',
          accent: '#0f3460',
        },
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      },
      animation: {
        'pulse-cyan': 'pulse-cyan 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'counter': 'counter 0.8s ease-out',
      },
      keyframes: {
        'pulse-cyan': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '.5' },
        },
        'counter': {
          '0%': { transform: 'scale(0.9)', opacity: '0' },
          '50%': { opacity: '1' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  daisyui: {
    themes: [
      {
        dark: {
          "primary": "#00d4ff",
          "secondary": "#16213e",
          "accent": "#0f3460",
          "neutral": "#1a1a2e",
          "base-100": "#1a1a2e",
          "base-200": "#16213e",
          "base-300": "#0f3460",
          "info": "#0ea5e9",
          "success": "#10b981",
          "warning": "#f59e0b",
          "error": "#ef4444",
        },
      },
    ],
  },
  plugins: [require('daisyui')],
};
