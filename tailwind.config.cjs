module.exports = {
  darkMode: 'class',
  content: [
    './index.html',
    './App.tsx',
    './components/**/*.{ts,tsx,jsx,js}',
    './services/**/*.{ts,tsx,js}'
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#0B1120',
          primary: '#06B6D4',
          secondary: '#8B5CF6',
          accent: '#10B981',
          surface: '#1E293B'
        }
      },
      fontFamily: {
        mono: ['ui-monospace','SFMono-Regular','Menlo','Monaco','Consolas','Liberation Mono','Courier New','monospace']
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite'
      }
    }
  },
  plugins: []
};
