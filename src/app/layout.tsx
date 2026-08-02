import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MCP Workbench — Test, Validate & Debug MCP Servers",
  description: "The Postman for Model Context Protocol servers. Connect, test tools, validate compatibility, and share configs with your team.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen">{children}</body>
    </html>
  );
}
