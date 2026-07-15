"use client";

import { useAuth } from "@/stores/auth";
import { PageHeader } from "@/components/layout/page-header";
import { Settings, User, Building, Globe, LogOut, Bot } from "lucide-react";

export default function SettingsPage() {
  const { user, logout } = useAuth();

  return (
    <div className="max-w-4xl mx-auto px-6 py-6">
      <PageHeader
        tag="Settings"
        title="系统设置"
        description="管理你的个人信息、组织和 AI 配置。"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="p-5 rounded-xl bg-[hsl(var(--card))] border">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-14 h-14 rounded-2xl bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center">
              <User className="h-7 w-7 text-brand-700 dark:text-brand-400" />
            </div>
            <div>
              <p className="font-semibold">{user?.name}</p>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">{user?.email}</p>
            </div>
          </div>
          <div className="text-sm space-y-2.5 pt-3 border-t">
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">角色</span>
              <span className="font-medium">{user?.role_name || "owner"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">语言</span>
              <span className="font-medium">{user?.language || "zh"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">时区</span>
              <span className="font-medium">{user?.timezone || "Asia/Singapore"}</span>
            </div>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-[hsl(var(--card))] border">
          <h2 className="text-sm font-semibold flex items-center gap-2 mb-4">
            <Building className="h-4 w-4 text-brand-600" /> 组织信息
          </h2>
          <div className="text-sm space-y-2.5">
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">组织名称</span>
              <span className="font-medium">AARON USA LLC</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">默认语言</span>
              <span className="font-medium">中文</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">部署区域</span>
              <span className="font-medium">Singapore</span>
            </div>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-[hsl(var(--card))] border">
          <h2 className="text-sm font-semibold flex items-center gap-2 mb-4">
            <Bot className="h-4 w-4 text-brand-600" /> AI 设置
          </h2>
          <div className="text-sm space-y-2.5">
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">CEO Agent 模型</span>
              <span className="font-medium">GPT-4o</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">Code Agent 模型</span>
              <span className="font-medium">Claude Sonnet</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">记忆自动确认</span>
              <span className="font-medium">关闭</span>
            </div>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-[hsl(var(--card))] border flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-semibold flex items-center gap-2 mb-2">
              <Settings className="h-4 w-4 text-brand-600" /> 系统
            </h2>
            <p className="text-xs text-[hsl(var(--muted-foreground))]">
              CEO Agent v1.0 · FastAPI + Next.js · Docker Compose
            </p>
          </div>
          <button
            onClick={logout}
            className="mt-4 w-full p-2.5 rounded-xl bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800/30 text-red-600 text-sm font-medium flex items-center justify-center gap-2 hover:bg-red-100 dark:hover:bg-red-900/20 transition-colors"
          >
            <LogOut className="h-4 w-4" /> 退出登录
          </button>
        </div>
      </div>
    </div>
  );
}
