import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ceat: {
          blue:      "#0055AA",
          "dark":    "#273C6F",
          orange:    "#F58220",
          "blue-50": "#EBF3FF",
          "blue-100":"#C2D9F5",
          "dark-80": "#3D5490",
        },
      },
      fontFamily: {
        display: ["var(--font-barlow)", "sans-serif"],
        body:    ["var(--font-ibm)", "sans-serif"],
        mono:    ["var(--font-mono)", "monospace"],
      },
      keyframes: {
        "fade-up": {
          "0%":   { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-dot": {
          "0%, 80%, 100%": { transform: "scale(0.6)", opacity: "0.4" },
          "40%":           { transform: "scale(1)",   opacity: "1"   },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0"  },
        },
      },
      animation: {
        "fade-up":   "fade-up 0.25s ease-out forwards",
        "pulse-dot": "pulse-dot 1.2s ease-in-out infinite",
        shimmer:     "shimmer 1.8s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
