import { createSystem, defaultConfig, defineConfig } from '@chakra-ui/react';

// Škoda Brand Colors
const skodaColors = {
  green: '#4da944',
  greenDark: '#3a8234',
  greenLight: '#6bc05f',
  navy: '#0d1b2a',
  navyLight: '#1a2f42',
  sand: '#f6f7f8',
  sandDark: '#e8eaec',
};

// Create a Chakra UI v3 system with Škoda brand configuration
const config = defineConfig({
  theme: {
    tokens: {
      colors: {
        skoda: {
          green: { value: skodaColors.green },
          greenDark: { value: skodaColors.greenDark },
          greenLight: { value: skodaColors.greenLight },
          navy: { value: skodaColors.navy },
          navyLight: { value: skodaColors.navyLight },
          sand: { value: skodaColors.sand },
          sandDark: { value: skodaColors.sandDark },
        },
        brand: {
          50: { value: '#e8f5e6' },
          100: { value: '#c3e5bf' },
          200: { value: '#9dd595' },
          300: { value: '#77c56b' },
          400: { value: '#5bb84c' },
          500: { value: skodaColors.green },
          600: { value: '#459a3d' },
          700: { value: skodaColors.greenDark },
          800: { value: '#306b2b' },
          900: { value: '#1f4619' },
        },
      },
      fonts: {
        heading: { value: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif' },
        body: { value: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif' },
      },
    },
    semanticTokens: {
      colors: {
        'skoda.green': { value: skodaColors.green },
        'skoda.greenDark': { value: skodaColors.greenDark },
        'skoda.greenLight': { value: skodaColors.greenLight },
        'skoda.navy': { value: skodaColors.navy },
        'skoda.navyLight': { value: skodaColors.navyLight },
        'skoda.sand': { value: skodaColors.sand },
        'skoda.sandDark': { value: skodaColors.sandDark },
      },
    },
  },
});

export const system = createSystem(defaultConfig, config);
export default system;
