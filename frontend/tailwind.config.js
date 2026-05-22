/** @type {import('tailwindcss').Config} */
export default {
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        ocean: "#155e75",
        mint: "#0f766e",
        amber: "#b45309",
        rose: "#be123c"
      }
    }
  },
  plugins: []
};
