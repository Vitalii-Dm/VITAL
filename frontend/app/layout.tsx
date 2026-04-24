import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VITAL",
  description: "Invisible guardian for warehouse workers",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
