"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  MessageSquare, LayoutDashboard, CheckSquare, FolderKanban,
  GitBranch, Brain, FileText, Bell, ShieldCheck, Bot,
  HeartPulse, ClipboardList, Settings, LogOut,
} from "lucide-react";
import { useAuth } from "@/stores/auth";

const navItems = [
  { href: "/chat", label: "CEO Agent", icon: MessageSquare },
  { href: "/daily", label: "今日经营", icon: LayoutDashboard },
  { href: "/tasks", label: "任务", icon: CheckSquare },
  { href: "/projects", label: "项目", icon: FolderKanban },
  { href: "/decisions", label: "决策", icon: GitBranch },
  { href: "/memories", label: "记忆", icon: Brain },
  { href: "/files", label: "文件", icon: FileText },
  { href: "/agents", label: "Agent 中心", icon: Bot },
  { href: "/heartbeat", label: "Heartbeat", icon: HeartPulse },
  { href: "/notifications", label: "通知", icon: Bell },
  { href: "/approvals", label: "审批", icon: ShieldCheck },
  { href: "/audit", label: "操作日志", icon: ClipboardList },
  { href: "/settings", label: "设置", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="hidden lg:flex flex-col w-60 border-r bg-[hsl(var(--card))] h-screen sticky top-0">
      <div className="p-4 border-b">
        <h1 className="text-lg font-bold text-brand-600">CEO Agent</h1>
        <p className="text-xs text-[hsl(var(--muted-foreground))] truncate">{user?.name}</p>
      </div>

      <nav className="flex-1 overflow-y-auto p-2 space-y-0.5 scrollbar-thin">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
              pathname === item.href
                ? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400 font-medium"
                : "text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))]"
            )}
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="p-2 border-t">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))] w-full"
        >
          <LogOut className="h-4 w-4" />
          退出登录
        </button>
      </div>
    </aside>
  );
}
