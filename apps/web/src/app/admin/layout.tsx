"use client";

import { AdminGuard, AdminSidebar } from "@/components/admin";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminGuard>
      <div className="flex min-h-[calc(100vh-4rem)] bg-[#0f1419]">
        <AdminSidebar />
        <div className="flex flex-1 flex-col overflow-hidden">{children}</div>
      </div>
    </AdminGuard>
  );
}
