/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'reroute-bg': {
          DEFAULT: '#0e1a2b', // fallback
          900: '#0e1a2b',
          800: '#142447',
          700: '#1a2e5c',
          600: '#223a6b',
        },
        'reroute-card': '#182544',
        'reroute-primary': '#6ec1e4',
        'reroute-accent': '#a7ffeb',
        'reroute-green': '#4ade80',
        'reroute-red': '#f87171',
        'reroute-yellow': '#fde68a',
        'reroute-purple': '#a78bfa',
        'reroute-gray': '#e5e7eb',
        'reroute-tab-active': '#a6c9d6',
        'reroute-tabbar': '#223a6b',
      },
      backgroundImage: {
        'reroute-gradient': 'linear-gradient(135deg, #0e1a2b 0%, #1a2e5c 50%, #223a6b 100%)',
      },
      boxShadow: {
        card: '0 4px 32px 0 rgba(16, 30, 54, 0.25)',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
}; 