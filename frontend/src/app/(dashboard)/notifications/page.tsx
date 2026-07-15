"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import { PageHeader } from "@/components/layout/page-header";
import { Bell, CheckCheck } from "lucide-react";
import type { Notification } from "@/types";

export default function NotificationsPage() {
  const queryClient = useQueryClient();

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.get<Notification[]>("/api/notifications"),
  });

  const markRead = useMutation({
    mutationFn: (id: string) => api.patch(`/api/notifications/${id}/read`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAllRead = useMutation({
    mutationFn: () => api.patch("/api/notifications/read-all"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <div className="max-w-4xl mx-auto px-6 py-6">
      <PageHeader
        tag="Notifications"
        title="通知中心"
        description="查看系统通知和 Agent 消息。"
        action={
          <button
            onClick={() => markAllRead.mutate()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))]"
          >
            <CheckCheck className="h-3.5 w-3.5" /> 全部已读
          </button>
        }
      />

      <div className="space-y-2">
        {notifications.map((n) => (
          <button
            key={n.id}
            onClick={() => !n.read_at && markRead.mutate(n.id)}
            className={`w-full text-left p-4 rounded-xl border text-sm transition-colors ${
              n.read_at ? "bg-[hsl(var(--card))]" : "bg-brand-50 dark:bg-brand-900/10 border-brand-200 dark:border-brand-800/30"
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                n.read_at ? "bg-[hsl(var(--muted))]" : "bg-brand-100 dark:bg-brand-900/30"
              }`}>
                <Bell className={`h-4 w-4 ${n.read_at ? "text-gray-400" : "text-brand-600"}`} />
              </div>
              <div className="flex-1">
                <p className="font-medium">{n.title}</p>
                {n.content && <p className="text-[hsl(var(--muted-foreground))] mt-0.5">{n.content}</p>}
                <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">{formatRelativeTime(n.created_at)}</p>
              </div>
            </div>
          </button>
        ))}
        {notifications.length === 0 && (
          <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-12">暂无通知</p>
        )}
      </div>
    </div>
  );
}
