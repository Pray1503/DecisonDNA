import type { Metadata } from "next";
import { DashboardShell } from "./shell";

export const metadata: Metadata = {
  title: "Dashboard — DecisionDNA AI",
  description:
    "Your AI-powered decision intelligence dashboard. Track architecture decisions, monitor integrations, and get AI-generated insights.",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DashboardShell>{children}</DashboardShell>;
}
