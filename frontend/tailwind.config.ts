import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f7f2",
          100: "#dceee2",
          200: "#bddcc8",
          300: "#90c4a2",
          400: "#5fa97a",
          500: "#3d8b5c",
          600: "#2d7049",
          700: "#245a3b",
          800: "#1f4830",
          900: "#1a3a28",
          950: "#0e2118",
        },
        gold: {
          50: "#fdf8ef",
          100: "#faefd5",
          200: "#f4dcaa",
          300: "#edc374",
          400: "#e5a63e",
          500: "#de9020",
          600: "#c97316",
          700: "#a75714",
          800: "#884518",
          900: "#703a17",
        },
      },
    },
  },
  plugins: [],
};
export default config;
