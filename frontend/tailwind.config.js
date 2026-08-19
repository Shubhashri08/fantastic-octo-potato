/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0A0A0A",
        surface: "#131313",
        "surface-container-lowest": "#0E0E0E",
        "surface-container-low": "#1C1B1B",
        "surface-container": "#201F1F",
        "surface-container-high": "#2A2A2A",
        "surface-container-highest": "#353534",
        primary: "#f5dfc0",
        "primary-container": "#d8c3a5",
        "on-primary": "#3b2e19",
        secondary: "#9ed1c1",
        "secondary-container": "#1d4f43",
        tertiary: "#ffd9d7",
        "tertiary-container": "#8e3335",
        outline: "#988f85",
        "outline-variant": "#4c463d",
        "on-surface": "#e5e2e1",
        "on-surface-variant": "#cfc5b9",
      },
      fontFamily: {
        sans: ["'Hanken Grotesk'", "Inter", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};
