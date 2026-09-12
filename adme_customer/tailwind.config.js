/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        bg: "#0f172a",
        surface: "#1e293b",
        primary: "#2563eb",
        muted: "#94a3b8",
        adminBg: "#f5f8f4",
        adminSurface: "#ffffff",
        adminPrimary: "#218b3a",
        adminDark: "#16351d",
        adminText: "#213a27",
        adminMuted: "#718075",
        adminBorder: "#e2ebe3",
        adminSoft: "#eaf5e9",
        adminField: "#fbfdfb",
        nearBg: "#f8f5ef",
        nearInk: "#24332b",
        nearAccent: "#e77745",
        nearSoft: "#f3d8bd",
        nearMuted: "#81786d",
        nearCard: "#fffdf9",
        nearBorder: "#e7dfd4",
        nearField: "#fffdf9",
      },
    },
  },
  plugins: [],
};
