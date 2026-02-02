import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: {
      center: true,
      padding: {
        DEFAULT: "1rem",
        sm: "2rem",
        lg: "4rem",
        xl: "5rem",
        "2xl": "6rem",
      },
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Teal scale
        teal: {
          50: "hsl(var(--teal-50))",
          100: "hsl(var(--teal-100))",
          200: "hsl(var(--teal-200))",
          300: "hsl(var(--teal-300))",
          400: "hsl(var(--teal-400))",
          500: "hsl(var(--teal-500))",
          600: "hsl(var(--teal-600))",
          700: "hsl(var(--teal-700))",
          800: "hsl(var(--teal-800))",
          900: "hsl(var(--teal-900))",
          950: "hsl(var(--teal-950))",
        },
        // Amber scale
        amber: {
          50: "hsl(var(--amber-50))",
          500: "hsl(var(--amber-500))",
          600: "hsl(var(--amber-600))",
        },
        // Parchment
        parchment: {
          50: "hsl(var(--parchment-50))",
          100: "hsl(var(--parchment-100))",
          200: "hsl(var(--parchment-200))",
        },
        // Archetype colors
        archetype: {
          fire: "hsl(var(--archetype-fire))",
          water: "hsl(var(--archetype-water))",
          lightning: "hsl(var(--archetype-lightning))",
          psychic: "hsl(var(--archetype-psychic))",
          fighting: "hsl(var(--archetype-fighting))",
          darkness: "hsl(var(--archetype-darkness))",
          metal: "hsl(var(--archetype-metal))",
          grass: "hsl(var(--archetype-grass))",
          dragon: "hsl(var(--archetype-dragon))",
          colorless: "hsl(var(--archetype-colorless))",
          fairy: "hsl(var(--archetype-fairy))",
        },
        // Tier colors
        tier: {
          s: "hsl(var(--tier-s))",
          a: "hsl(var(--tier-a))",
          b: "hsl(var(--tier-b))",
          c: "hsl(var(--tier-c))",
          rogue: "hsl(var(--tier-rogue))",
        },
        // Signal colors
        signal: {
          up: "hsl(var(--signal-up))",
          down: "hsl(var(--signal-down))",
          stable: "hsl(var(--signal-stable))",
          jp: "hsl(var(--signal-jp))",
        },
        // Terminal panel
        terminal: {
          bg: "hsl(var(--terminal-bg))",
          surface: "hsl(var(--terminal-surface))",
          border: "hsl(var(--terminal-border))",
          text: "hsl(var(--terminal-text))",
          muted: "hsl(var(--terminal-muted))",
          accent: "hsl(var(--terminal-accent))",
        },
        // Notebook palette (Field Notebook aesthetic)
        notebook: {
          cream: "hsl(var(--notebook-cream))",
          grid: "hsl(var(--notebook-grid))",
          aged: "hsl(var(--notebook-aged))",
        },
        ink: {
          black: "hsl(var(--ink-black))",
          red: "hsl(var(--ink-red))",
        },
        pencil: "hsl(var(--pencil-gray))",
      },
      fontFamily: {
        display: ["var(--font-display)"],
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
      fontSize: {
        display: ["3rem", { lineHeight: "3.5rem", fontWeight: "700" }],
        h1: ["2.25rem", { lineHeight: "2.75rem", fontWeight: "600" }],
        h2: ["1.5rem", { lineHeight: "2rem", fontWeight: "600" }],
        h3: ["1.125rem", { lineHeight: "1.75rem", fontWeight: "500" }],
        body: ["1rem", { lineHeight: "1.5rem", fontWeight: "400" }],
        small: ["0.875rem", { lineHeight: "1.25rem", fontWeight: "400" }],
        mono: ["0.875rem", { lineHeight: "1.25rem", fontWeight: "400" }],
        "mono-sm": ["0.75rem", { lineHeight: "1rem", fontWeight: "400" }],
      },
      spacing: {
        "panel-width": "480px",
        "section-px": "24px",
        "section-py": "16px",
        "element-gap": "12px",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
