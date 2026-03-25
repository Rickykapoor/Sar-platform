import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SAR Platform — AI-Powered AML Intelligence",
  description: "Automated Suspicious Activity Report generation for Indian banks.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-black text-white antialiased">{children}</body>
    </html>
  );
}
