import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IFM Tyre Advisor — CEAT",
  description: "AI-powered In-Fleet Management tyre analytics for CEAT",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
