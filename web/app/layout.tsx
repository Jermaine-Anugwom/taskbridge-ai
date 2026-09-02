import type { Metadata } from "next";
import localFont from "next/font/local";
import "./style.css";

const archivo = localFont({
  src: "./fonts/Archivo-Variable.ttf",
  variable: "--font-display",
  display: "swap",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "TaskBridge AI | Workflow Workshop",
  description: "Map repetitive work, choose the right intervention, and simulate a controlled pilot.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={archivo.variable}>{children}</body>
    </html>
  );
}
