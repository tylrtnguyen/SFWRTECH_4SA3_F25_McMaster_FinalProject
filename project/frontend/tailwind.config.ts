import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary colors - JobTrust Theme
        primary: {
          400: "#3d8fd7",
          500: "#2a7abc",
          600: "#0a66c2",
          700: "#084d92",
          DEFAULT: "#0a66c2",
          foreground: "#ffffff",
        },
        
        // Secondary colors - JobTrust Theme
        secondary: {
          400: "#4dd4cb",
          600: "#00b2a9",
          DEFAULT: "#00b2a9",
          foreground: "#ffffff",
        },
        
        // Success colors - JobTrust Theme
        success: {
          400: "#57D9A3",
          600: "#36B37E",
          DEFAULT: "#36B37E",
          foreground: "#ffffff",
        },
        
        // Accent/Warning colors - JobTrust Theme
        accent: {
          warning: "#eed971",
          DEFAULT: "#eed971",
          foreground: "#172B4D",
        },
        
        // Background colors - JobTrust Theme (light mode defaults)
        "bg-primary": "#FFFFFF",
        "bg-secondary": "#F4F5F7",
        "bg-tertiary": "#FFFFFF",
        
        // Text colors - JobTrust Theme (light mode defaults)
        "text-primary": "#172B4D",
        "text-secondary": "#5E6C84",
        "text-tertiary": "#8993A4",
        
        // Border colors
        border: {
          default: "#DFE1E6",
          DEFAULT: "#DFE1E6",
        },
        
        // Legacy shadcn/ui compatibility (light mode defaults)
        background: "#FFFFFF",
        foreground: "#172B4D",
        muted: {
          DEFAULT: "#F4F5F7",
          foreground: "#5E6C84",
        },
        destructive: {
          DEFAULT: "#ef4444",
          foreground: "#ffffff",
        },
        card: {
          DEFAULT: "#F4F5F7",
          foreground: "#172B4D",
        },
        popover: {
          DEFAULT: "#FFFFFF",
          foreground: "#172B4D",
        },
        input: "#DFE1E6",
        ring: "#0a66c2",
      },
      borderRadius: {
        lg: "0.5rem",
        md: "calc(0.5rem - 2px)",
        sm: "calc(0.5rem - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
