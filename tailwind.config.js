/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./*.html",
    "./blog/*.html",
  ],
  theme: {
    extend: {
      colors: {
        eggshell: '#F7F3EE',
        charcoal: '#1C1C1C',
        burgundy: { DEFAULT: '#7D2240', dark: '#651B33', deeper: '#3D1020' },
        gold: { DEFAULT: '#C9A847', dark: '#B8952E', muted: '#D4B96A' },
        surface: '#FFFFFF',
        muted: '#6B6560',
      },
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
      letterSpacing: {
        tightest: '-0.03em',
        widest2: '0.12em',
      },
    },
  },
  plugins: [],
}
