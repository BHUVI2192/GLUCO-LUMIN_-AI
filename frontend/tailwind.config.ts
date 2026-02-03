import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#0F172A", // Slate 900
        secondary: "#334155", // Slate 700
        accent: "#3B82F6", // Blue 500
        success: "#10B981", // Emerald 500
        warning: "#F59E0B", // Amber 500
        danger: "#EF4444", // Red 500
      },
    },
  },
  plugins: [],
};
export default config;
