/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: 'var(--color-bg)',
        surface: 'var(--color-surface)',
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        success: 'var(--color-success)',
        error: 'var(--color-error)',
        info: 'var(--color-info)',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Nunito Sans', 'sans-serif'],
      },
      boxShadow: {
        'glow': '0 0 20px rgba(0, 178, 255, 0.3)',
      }
    },
  },
  plugins: [],
}
