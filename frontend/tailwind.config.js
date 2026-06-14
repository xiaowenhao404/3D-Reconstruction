/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0b0f17',
        panel: '#131a26',
        accent: '#5b9dff',
      },
    },
  },
  plugins: [],
};
