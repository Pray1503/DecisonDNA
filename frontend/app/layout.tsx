import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DecisionDNA AI — Enterprise Decision Intelligence Platform",
  description:
    "Transforming organizational decisions into living intelligence. Access your team's AI-powered knowledge graph, ADRs, GitHub insights, and Jira intelligence.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-navy-950 text-white antialiased">{children}</body>
    </html>
  );
}
