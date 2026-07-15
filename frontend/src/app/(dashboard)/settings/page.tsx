"use client";

import { useAuth } from "@/stores/auth";
import { Settings, User, Building, Globe, LogOut } from "lucide-react";

export default function SettingsPage() {
  const { user, logout } = useAuth();

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <h1 className="text-xl font-bold">设置</h1>

      <div className="space-y-3">
        <div className="p-4 rounded-xl bg-[hsl(var(--card))] border">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center">
              <User className="h-6 w-6 text-brand-600" />
            </div>
            <div>
              <p className="font-medium">{user?.name}</p>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">{user?.email}</p>
            </div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[hsl(var(--card))] border space-y-4">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <Building className="h-4 w-4" /> 组织信息
          </h2>
          <div className="text-sm space-y-2">
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">角色</span>
              <span>{user?.role_name || "owner"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">语言</span>
              <span>{user?.language || "zh"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">时区</span>
              <span>{user?.timezone || "Asia/Singapore"}</span>
            </div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[hsl(var(--card))] border space-y-4">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <Settings className="h-4 w-4" /> AI 设置
          </h2>
          <div className="text-sm space-y-2">
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">默认模型</span>
              <span>GPT-4o</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">记忆自动确认</span>
              <span>关闭</span>
            </div>
          </div>
        </div>

        <button
          onClick={logout}
          className="w-full p-3 rounded-xl bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800/30 text-red-600 text-sm font-medium flex items-center justify-center gap-2"
        >
          <LogOut className="h-4 w-4" /> 退出登录
        </button>
      </div>
    </div>
  );
}
