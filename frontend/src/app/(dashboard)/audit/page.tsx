"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import { ClipboardList } from "lucide-react";

interface AuditLog {
  id: string;
  user_id: string | null;
  agent_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  ip_address: string | null;
  created_at: string;
}

export default function AuditPage() {
  const { data: logs = [] } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => api.get<AuditLog[]>("/api/audit-logs"),
  });

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      <h1 className="text-xl font-bold">操作日志</h1>

      <div className="space-y-1">
        {logs.map((log) => (
          <div key={log.id} className="p-3 rounded-lg bg-[hsl(var(--card))] border text-sm flex items-center gap-3">
            <ClipboardList className="h-4 w-4 text-[hsl(var(--muted-foreground))] shrink-0" />
            <div className="flex-1 min-w-0">
              <span className="font-medium">{log.action}</span>
              <span className="text-[hsl(var(--muted-foreground))]"> · {log.resource_type}</span>
            </div>
            <span className="text-xs text-[hsl(var(--muted-foreground))] whitespace-nowrap">
              {formatRelativeTime(log.created_at)}
            </span>
          </div>
        ))}
        {logs.length === 0 && (
          <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-8">暂无操作日志</p>
        )}
      </div>
    </div>
  );
}
