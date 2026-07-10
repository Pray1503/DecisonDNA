"use client";

import { Sidebar } from "@/components/dashboard/sidebar";
import { TopBar } from "@/components/dashboard/top-bar";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-navy-950 text-white">
      <Sidebar />
      <div className="ml-[240px]">
        <TopBar />
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
}
