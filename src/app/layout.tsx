import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://mcp-workbench.uk"),
  title: {
    default: "MCP Workbench — Test, Validate & Debug MCP Servers",
    template: "%s | MCP Workbench",
  },
  description:
    "The Postman for Model Context Protocol servers. Connect to any MCP server in your browser, test tools visually, debug JSON-RPC traffic, and validate compatibility with Claude, Cursor, and VS Code. No terminal needed.",
  keywords: [
    "MCP server testing",
    "Model Context Protocol",
    "MCP debugger",
    "MCP validator",
    "test MCP server online",
    "MCP tools",
    "Claude MCP",
    "Cursor MCP",
    "MCP compatibility",
  ],
  openGraph: {
    type: "website",
    url: "https://mcp-workbench.uk",
    siteName: "MCP Workbench",
    title: "MCP Workbench — The Postman for MCP Servers",
    description:
      "Connect, test, validate, and debug Model Context Protocol servers in your browser. No config files. No terminal gymnastics.",
    locale: "en_GB",
  },
  twitter: {
    card: "summary_large_image",
    title: "MCP Workbench — The Postman for MCP Servers",
    description:
      "Connect, test, validate, and debug Model Context Protocol servers in your browser.",
    creator: "@Gizmo50009",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: "https://mcp-workbench.uk",
  },
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
