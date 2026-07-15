"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
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
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">通知</h1>
        <button
          onClick={() => markAllRead.mutate()}
          className="flex items-center gap-1 text-sm text-brand-600 hover:underline"
        >
          <CheckCheck className="h-4 w-4" /> 全部已读
        </button>
      </div>

      <div className="space-y-2">
        {notifications.map((n) => (
          <button
            key={n.id}
            onClick={() => !n.read_at && markRead.mutate(n.id)}
            className={`w-full text-left p-3 rounded-xl border text-sm transition-colors ${
              n.read_at ? "bg-[hsl(var(--card))]" : "bg-brand-50 dark:bg-brand-900/10 border-brand-200"
            }`}
          >
            <div className="flex items-start gap-3">
              <Bell className={`h-4 w-4 mt-0.5 shrink-0 ${n.read_at ? "text-gray-400" : "text-brand-500"}`} />
              <div>
                <p className="font-medium">{n.title}</p>
                {n.content && <p className="text-[hsl(var(--muted-foreground))] mt-0.5">{n.content}</p>}
                <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">{formatRelativeTime(n.created_at)}</p>
              </div>
            </div>
          </button>
        ))}
        {notifications.length === 0 && (
          <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-8">暂无通知</p>
        )}
      </div>
    </div>
  );
}
