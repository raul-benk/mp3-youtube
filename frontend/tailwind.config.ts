import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./lib/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"]
      },
      colors: {
        bgStart: "#f4f7f1",
        bgEnd: "#dff4ea",
        card: "#fdfcf9",
        primary: "#0b6e4f",
        accent: "#f08a24"
      },
      boxShadow: {
        card: "0 10px 30px rgba(9, 38, 30, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
