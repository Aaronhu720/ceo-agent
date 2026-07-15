"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  AlertTriangle, CheckCircle2, Clock, Bell,
  Camera, Mic, FileText, TrendingUp,
} from "lucide-react";
import type { Task, Notification } from "@/types";
import Link from "next/link";

export default function DailyPage() {
  const { data: tasks = [] } = useQuery({
    queryKey: ["tasks", "active"],
    queryFn: () => api.get<Task[]>("/api/tasks?status_filter=in_progress"),
  });

  const { data: pendingTasks = [] } = useQuery({
    queryKey: ["tasks", "pending"],
    queryFn: () => api.get<Task[]>("/api/tasks?status_filter=pending"),
  });

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.get<Notification[]>("/api/notifications?unread_only=true"),
  });

  const today = new Date();

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold">今日经营</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">{formatDate(today)}</p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-3 gap-3">
        <Link href="/chat" className="flex flex-col items-center gap-1.5 p-4 rounded-xl bg-[hsl(var(--card))] border hover:border-brand-300 transition-colors">
          <FileText className="h-6 w-6 text-brand-500" />
          <span className="text-xs">快速记录</span>
        </Link>
        <button className="flex flex-col items-center gap-1.5 p-4 rounded-xl bg-[hsl(var(--card))] border hover:border-brand-300 transition-colors">
          <Camera className="h-6 w-6 text-green-500" />
          <span className="text-xs">拍照</span>
        </button>
        <button className="flex flex-col items-center gap-1.5 p-4 rounded-xl bg-[hsl(var(--card))] border hover:border-brand-300 transition-colors">
          <Mic className="h-6 w-6 text-purple-500" />
          <span className="text-xs">语音</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-4 rounded-xl bg-[hsl(var(--card))] border">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="h-4 w-4 text-orange-500" />
            <span className="text-xs text-[hsl(var(--muted-foreground))]">进行中</span>
          </div>
          <p className="text-2xl font-bold">{tasks.length}</p>
        </div>
        <div className="p-4 rounded-xl bg-[hsl(var(--card))] border">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="h-4 w-4 text-red-500" />
            <span className="text-xs text-[hsl(var(--muted-foreground))]">待处理</span>
          </div>
          <p className="text-2xl font-bold">{pendingTasks.length}</p>
        </div>
      </div>

      {/* Notifications */}
      {notifications.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <Bell className="h-4 w-4" /> 最新通知
          </h2>
          {notifications.slice(0, 5).map((n) => (
            <div key={n.id} className="p-3 rounded-xl bg-[hsl(var(--card))] border text-sm">
              <p className="font-medium">{n.title}</p>
              {n.content && <p className="text-[hsl(var(--muted-foreground))] mt-1">{n.content}</p>}
            </div>
          ))}
        </div>
      )}

      {/* Today's tasks */}
      <div className="space-y-2">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" /> 今日任务
        </h2>
        {tasks.length === 0 && pendingTasks.length === 0 ? (
          <p className="text-sm text-[hsl(var(--muted-foreground))] p-4 text-center">暂无任务</p>
        ) : (
          [...tasks, ...pendingTasks].slice(0, 10).map((task) => (
            <Link
              key={task.id}
              href="/tasks"
              className="block p-3 rounded-xl bg-[hsl(var(--card))] border text-sm hover:border-brand-300 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">{task.title}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  task.priority === "high" ? "bg-red-100 text-red-700" :
                  task.priority === "medium" ? "bg-yellow-100 text-yellow-700" :
                  "bg-green-100 text-green-700"
                }`}>{task.priority}</span>
              </div>
              {task.due_date && (
                <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">截止: {task.due_date}</p>
              )}
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
