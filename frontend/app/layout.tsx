import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Universal Stock API",
  description: "Enterprise-grade Inventory Management System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
