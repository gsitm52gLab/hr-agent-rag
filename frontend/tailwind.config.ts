import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        dark: {
          DEFAULT: "#1a1a2e",
          light: "#16213e",
          lighter: "#0f3460",
        },
        accent: {
          purple: "#7c3aed",
          blue: "#2563eb",
          gradient: "linear-gradient(135deg, #7c3aed, #2563eb)",
        },
        surface: {
          DEFAULT: "#1e1e3a",
          hover: "#2a2a4a",
          border: "#333366",
        },
      },
      fontFamily: {
        sans: ["Inter", "Pretendard", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
