"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  MessageSquare, LayoutDashboard, CheckSquare, FolderKanban,
  GitBranch, Brain, AlertTriangle, Bot,
  HeartPulse, Bell, LogOut, Store,
} from "lucide-react";
import { useAuth } from "@/stores/auth";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Task, Decision, Notification } from "@/types";

const navGroups = [
  {
    label: "经营决策中心",
    items: [
      { href: "/daily", label: "CEO 工作台", icon: LayoutDashboard },
      { href: "/chat", label: "AI 对话助手", icon: MessageSquare },
    ],
  },
  {
    label: "执行管理",
    items: [
      { href: "/decisions", label: "待决策事项", icon: GitBranch, badgeKey: "decisions" as const },
      { href: "/tasks", label: "任务与项目看板", icon: CheckSquare },
      { href: "/projects", label: "项目管理", icon: FolderKanban },
    ],
  },
  {
    label: "渠道管理",
    items: [
      { href: "/mercadolibre", label: "Mercado Libre", icon: Store },
    ],
  },
  {
    label: "智能系统",
    items: [
      { href: "/memories", label: "长期记忆库", icon: Brain },
      { href: "/agents", label: "多 Agent 协作", icon: Bot },
      { href: "/heartbeat", label: "风险雷达", icon: AlertTriangle, badgeKey: "risks" as const },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const { data: pendingDecisions = [] } = useQuery({
    queryKey: ["decisions-badge"],
    queryFn: () => api.get<Decision[]>("/api/decisions?status_filter=proposed"),
    refetchInterval: 60000,
  });

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications-badge"],
    queryFn: () => api.get<Notification[]>("/api/notifications?unread_only=true"),
    refetchInterval: 60000,
  });

  const badges: Record<string, number> = {
    decisions: pendingDecisions.length,
    risks: 0,
  };

  return (
    <aside className="hidden lg:flex flex-col w-60 h-screen sticky top-0 bg-[hsl(var(--sidebar))]">
      <div className="p-4 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[hsl(var(--sidebar-muted))] flex items-center justify-center">
            <LayoutDashboard className="h-4 w-4 text-[hsl(var(--sidebar-accent))]" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-[hsl(var(--sidebar-foreground))]">CEO Agent</h1>
            <p className="text-[10px] tracking-wider uppercase text-[hsl(var(--sidebar-accent))]">Executive Office</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 pb-2 scrollbar-thin space-y-4">
        {navGroups.map((group) => (
          <div key={group.label}>
            <p className="text-[10px] font-medium tracking-wider uppercase text-[hsl(var(--sidebar-foreground))]/50 px-2 mb-1.5">
              {group.label}
            </p>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const isActive = pathname === item.href;
                const badge = item.badgeKey ? badges[item.badgeKey] : 0;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[13px] transition-colors",
                      isActive
                        ? "bg-[hsl(var(--sidebar-muted))] text-[hsl(var(--sidebar-foreground))] font-medium"
                        : "text-[hsl(var(--sidebar-foreground))]/70 hover:bg-[hsl(var(--sidebar-muted))]/50 hover:text-[hsl(var(--sidebar-foreground))]"
                    )}
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    <span className="flex-1">{item.label}</span>
                    {badge > 0 && (
                      <span className="min-w-[18px] h-[18px] flex items-center justify-center rounded-full bg-[hsl(var(--sidebar-accent))] text-[hsl(var(--sidebar))] text-[10px] font-bold px-1">
                        {badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {notifications.length > 0 && (
        <div className="mx-3 mb-2 px-2.5 py-2 rounded-lg bg-[hsl(var(--sidebar-muted))]/50">
          <Link href="/notifications" className="flex items-center gap-2 text-[hsl(var(--sidebar-foreground))]/70 hover:text-[hsl(var(--sidebar-foreground))] text-[13px]">
            <Bell className="h-4 w-4" />
            <span>{notifications.length} 条未读通知</span>
          </Link>
        </div>
      )}

      <div className="p-3 border-t border-[hsl(var(--sidebar-muted))]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-[hsl(var(--sidebar-muted))] flex items-center justify-center text-[hsl(var(--sidebar-accent))] text-xs font-bold">
            {user?.name?.charAt(0) || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] font-medium text-[hsl(var(--sidebar-foreground))] truncate">{user?.name}</p>
            <p className="text-[10px] text-[hsl(var(--sidebar-foreground))]/50 truncate">AARON USA LLC</p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg hover:bg-[hsl(var(--sidebar-muted))] text-[hsl(var(--sidebar-foreground))]/50 hover:text-[hsl(var(--sidebar-foreground))]"
            title="退出登录"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
