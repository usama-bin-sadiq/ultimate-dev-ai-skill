/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "rgb(var(--surface) / <alpha-value>)",
        "surface-raised": "rgb(var(--surface-raised) / <alpha-value>)",
        ink: "rgb(var(--ink) / <alpha-value>)",
        "ink-muted": "rgb(var(--ink-muted) / <alpha-value>)",
        line: "rgb(var(--line) / <alpha-value>)",
        brand: "rgb(var(--brand) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
