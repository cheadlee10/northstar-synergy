/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // Custom color palette with WCAG AA compliance
      colors: {
        // Dark theme base
        dark: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#2d3748',
          800: '#1f2937',
          900: '#111827',
          950: '#1a1a2e', // NorthStar base
        },
        // Accent colors (cyan)
        accent: {
          DEFAULT: '#00d4ff',
          light: '#4df9ff',
          dark: '#00a8cc',
          50: '#f0fdfb',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
        // Semantic colors
        gain: {
          DEFAULT: '#16A34A',
          light: '#4ade80',
          dark: '#15803d',
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#145231',
        },
        loss: {
          DEFAULT: '#DC2626',
          light: '#f87171',
          dark: '#b91c1c',
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        alert: {
          DEFAULT: '#EA580C',
          light: '#fb923c',
          dark: '#c2410c',
          50: '#fef3c7',
          100: '#fde68a',
          200: '#fcd34d',
          300: '#fbbf24',
          400: '#f59e0b',
          500: '#f97316',
          600: '#ea580c',
          700: '#c2410c',
          800: '#92400e',
          900: '#78350f',
        },
        neutral: {
          DEFAULT: '#6B7280',
          light: '#9ca3af',
          dark: '#4b5563',
        },
        // Backgrounds
        bg: {
          primary: '#1a1a2e',
          secondary: '#16213e',
          tertiary: '#0f3460',
          surface: '#2d2d44',
        },
      },
      // Responsive breakpoints
      screens: {
        xs: '320px',
        sm: '480px',
        md: '768px',
        lg: '1024px',
        xl: '1280px',
        '2xl': '1536px',
      },
      // Custom spacing for touch targets
      spacing: {
        touch: '2.75rem', // 44px for touch targets
        18: '4.5rem',
        22: '5.5rem',
        26: '6.5rem',
      },
      // Custom animations
      keyframes: {
        'hover-lift': {
          '0%': { transform: 'translateY(0)', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)' },
          '100%': { transform: 'translateY(-4px)', boxShadow: '0 20px 25px rgba(0, 212, 255, 0.2)' },
        },
        'pulse-alert': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 0 0 rgba(234, 88, 12, 0.7)' },
          '50%': { opacity: '0.8', boxShadow: '0 0 0 10px rgba(234, 88, 12, 0)' },
        },
        'shimmer-skeleton': {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        'glow-update': {
          '0%, 100%': { boxShadow: '0 0 5px rgba(0, 212, 255, 0.5)' },
          '50%': { boxShadow: '0 0 20px rgba(0, 212, 255, 0.8)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'scale-pop': {
          '0%': { transform: 'scale(0.9)', opacity: '0' },
          '50%': { transform: 'scale(1.05)' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        'slide-in': {
          '0%': { transform: 'translateX(-20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        bounce: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      animation: {
        'hover-lift': 'hover-lift 0.2s ease-out',
        'pulse-alert': 'pulse-alert 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer-skeleton': 'shimmer-skeleton 2s infinite',
        'glow-update': 'glow-update 2s ease-in-out infinite',
        'fade-in': 'fade-in 0.3s ease-in',
        'scale-pop': 'scale-pop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'slide-in': 'slide-in 0.3s ease-out',
        bounce: 'bounce 1s infinite',
      },
      // Typography
      typography: {
        DEFAULT: {
          css: {
            color: '#ffffff',
            '[class~="lead"]': {
              color: '#9ca3af',
            },
            strong: {
              color: '#ffffff',
            },
            'ol > li::before': {
              color: '#6b7280',
            },
            'ul > li::before': {
              backgroundColor: '#00d4ff',
            },
            hr: {
              borderColor: '#374151',
            },
            blockquote: {
              color: '#9ca3af',
              borderLeftColor: '#00d4ff',
            },
            h1: { color: '#ffffff' },
            h2: { color: '#ffffff' },
            h3: { color: '#ffffff' },
            h4: { color: '#ffffff' },
            'figure figcaption': {
              color: '#6b7280',
            },
            code: {
              color: '#00d4ff',
              backgroundColor: '#1f2937',
              paddingLeft: '0.25rem',
              paddingRight: '0.25rem',
              borderRadius: '0.25rem',
            },
            'a code': {
              color: '#00d4ff',
            },
            pre: {
              color: '#e5e7eb',
              backgroundColor: '#111827',
            },
            thead: {
              color: '#ffffff',
              borderBottomColor: '#4b5563',
            },
            'tbody tr': {
              borderBottomColor: '#2d3748',
            },
            'tbody tr:last-child': {
              borderBottomWidth: '1px',
            },
          },
        },
      },
      // Shadow with cyan glow
      boxShadow: {
        'glow-cyan': '0 0 20px rgba(0, 212, 255, 0.3)',
        'glow-cyan-lg': '0 0 30px rgba(0, 212, 255, 0.5)',
        'glow-gain': '0 0 20px rgba(22, 163, 74, 0.3)',
        'glow-loss': '0 0 20px rgba(220, 38, 38, 0.3)',
        'glow-alert': '0 0 20px rgba(234, 88, 12, 0.3)',
      },
      // Transitions
      transitionDuration: {
        DEFAULT: '150ms',
      },
      // Font configuration for accessibility
      fontSize: {
        xs: ['0.75rem', { lineHeight: '1rem' }],
        sm: ['0.875rem', { lineHeight: '1.25rem' }],
        base: ['1rem', { lineHeight: '1.5rem' }],
        lg: ['1.125rem', { lineHeight: '1.75rem' }],
        xl: ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      },
      // Custom opacity for accessibility
      opacity: {
        0: '0',
        5: '0.05',
        10: '0.1',
        20: '0.2',
        25: '0.25',
        30: '0.3',
        40: '0.4',
        50: '0.5',
        60: '0.6',
        70: '0.7',
        75: '0.75',
        80: '0.8',
        90: '0.9',
        95: '0.95',
        100: '1',
      },
    },
  },
  plugins: [
    require('daisyui'),
    // Custom plugin for WCAG AA compliance utilities
    function ({ addComponents, theme }) {
      addComponents({
        '.visually-hidden': {
          position: 'absolute',
          width: '1px',
          height: '1px',
          padding: '0',
          margin: '-1px',
          overflow: 'hidden',
          clip: 'rect(0, 0, 0, 0)',
          whiteSpace: 'nowrap',
          borderWidth: '0',
        },
        '.focus-ring': {
          '@apply outline outline-2 outline-offset-2 outline-accent': {},
        },
        '.touch-target': {
          '@apply min-h-touch min-w-touch': {},
        },
      });
    },
  ],
  daisyui: {
    styled: true,
    themes: [
      {
        northstar: {
          'primary': '#00d4ff',
          'primary-content': '#1a1a2e',
          'secondary': '#6B7280',
          'secondary-content': '#ffffff',
          'accent': '#00d4ff',
          'accent-content': '#1a1a2e',
          'neutral': '#2d3748',
          'neutral-content': '#ffffff',
          'base-100': '#1a1a2e',
          'base-200': '#16213e',
          'base-300': '#0f3460',
          'base-content': '#ffffff',
          'info': '#00d4ff',
          'success': '#16A34A',
          'warning': '#EA580C',
          'error': '#DC2626',
          '--rounded-box': '0.5rem',
          '--rounded-btn': '0.375rem',
          '--rounded-badge': '1.9rem',
          '--animation-btn': '0.25s',
          '--animation-input': '0.2s',
          '--btn-text-case': 'uppercase',
          '--navbar-padding': '1rem',
          '--navbar-text-btn-pad': '0.6rem 1rem',
        },
      },
    ],
    base: true,
    utils: true,
    logs: false,
  },
};
