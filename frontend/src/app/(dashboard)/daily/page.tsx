"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import {
  TrendingUp, Users, AlertTriangle, BarChart3,
  ArrowUpRight, ArrowDownRight, CheckCircle2, Clock,
  Brain, GitBranch, ChevronRight, RefreshCw, Sparkles, Loader2,
} from "lucide-react";
import type { Task, Decision, Memory, Project, Notification } from "@/types";
import Link from "next/link";

function getGreeting() {
  const h = new Date().getHours();
  if (h < 6) return "夜深了";
  if (h < 12) return "早上好";
  if (h < 14) return "中午好";
  if (h < 18) return "下午好";
  return "晚上好";
}

function StatCard({ icon: Icon, label, value, trend, trendUp, color }: {
  icon: React.ElementType; label: string; value: string | number;
  trend?: string; trendUp?: boolean; color: string;
}) {
  return (
    <div className="p-4 rounded-xl bg-[hsl(var(--card))] border">
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${color}`}>
          <Icon className="h-4 w-4" />
        </div>
        <span className="text-xs text-[hsl(var(--muted-foreground))]">{label}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
      {trend && (
        <div className={`flex items-center gap-1 mt-1 text-xs ${trendUp ? "text-green-600" : "text-red-500"}`}>
          {trendUp ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
          {trend}
        </div>
      )}
    </div>
  );
}

interface DailyBriefing {
  id: string;
  log_date: string;
  summary: string | null;
  tasks_json: Record<string, unknown> | null;
  risks_json: Record<string, unknown> | null;
  decisions_json: Record<string, unknown> | null;
  confirmed_by_user: boolean;
  created_at: string;
}

export default function DailyPage() {
  const queryClient = useQueryClient();

  const { data: tasks = [] } = useQuery({
    queryKey: ["tasks-all"],
    queryFn: () => api.get<Task[]>("/api/tasks"),
  });

  const { data: decisions = [] } = useQuery({
    queryKey: ["decisions"],
    queryFn: () => api.get<Decision[]>("/api/decisions"),
  });

  const { data: memories = [] } = useQuery({
    queryKey: ["memories"],
    queryFn: () => api.get<Memory[]>("/api/memories"),
  });

  const { data: projects = [] } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.get<Project[]>("/api/projects"),
  });

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.get<Notification[]>("/api/notifications?unread_only=true"),
  });

  const { data: todayBriefing } = useQuery({
    queryKey: ["daily-log-today"],
    queryFn: () => api.get<DailyBriefing | null>("/api/daily-logs/today"),
  });

  const generateBriefing = useMutation({
    mutationFn: () => api.post<{ summary: string }>("/api/daily-logs/generate"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["daily-log-today"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const activeTasks = tasks.filter(t => t.status === "in_progress");
  const pendingDecisions = decisions.filter(d => d.decision_status === "proposed");
  const confirmedMemories = memories.filter(m => m.status === "confirmed");
  const activeProjects = projects.filter(p => p.status === "active");
  const atRiskTasks = tasks.filter(t => t.risk_level === "high" || t.status === "at_risk");

  const today = new Date();
  const dateStr = `${today.getFullYear()}年${today.getMonth()+1}月${today.getDate()}日`;

  return (
    <div className="max-w-6xl mx-auto px-6 py-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <p className="text-xs font-semibold tracking-wider uppercase text-brand-600 mb-1">CEO Agent</p>
          <h1 className="text-2xl font-bold">{getGreeting()}，Aaron</h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">
            {dateStr} · 以下是你的经营概览
          </p>
        </div>
        <button
          onClick={() => {
            queryClient.invalidateQueries({ queryKey: ["tasks-all"] });
            queryClient.invalidateQueries({ queryKey: ["decisions"] });
            queryClient.invalidateQueries({ queryKey: ["projects"] });
            queryClient.invalidateQueries({ queryKey: ["memories"] });
            queryClient.invalidateQueries({ queryKey: ["notifications"] });
            queryClient.invalidateQueries({ queryKey: ["daily-log-today"] });
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))] transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          更新数据
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard
              icon={BarChart3} label="活跃项目" value={activeProjects.length}
              color="bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400"
            />
            <StatCard
              icon={TrendingUp} label="进行中任务" value={activeTasks.length}
              color="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
            />
            <StatCard
              icon={Users} label="记忆条目" value={confirmedMemories.length}
              color="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400"
            />
            <StatCard
              icon={AlertTriangle} label="风险事项" value={atRiskTasks.length}
              trend={atRiskTasks.length > 0 ? "需要关注" : "无风险"}
              trendUp={atRiskTasks.length === 0}
              color="bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400"
            />
          </div>

          {/* AI Summary Card */}
          <div className="p-5 rounded-xl bg-brand-900 text-white dark:bg-brand-950">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-brand-300" />
                <span className="text-sm font-semibold text-brand-200">CEO Agent 经营简报</span>
              </div>
              <button
                onClick={() => generateBriefing.mutate()}
                disabled={generateBriefing.isPending}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-700 hover:bg-brand-600 text-xs text-brand-200 hover:text-white transition-colors disabled:opacity-50"
              >
                {generateBriefing.isPending ? (
                  <><Loader2 className="h-3 w-3 animate-spin" /> 生成中...</>
                ) : (
                  <><Sparkles className="h-3 w-3" /> {todayBriefing?.summary ? "重新生成" : "生成简报"}</>
                )}
              </button>
            </div>
            {todayBriefing?.summary ? (
              <div className="text-sm leading-relaxed text-brand-100 whitespace-pre-line">
                {todayBriefing.summary}
              </div>
            ) : (
              <p className="text-sm leading-relaxed text-brand-100">
                {activeTasks.length > 0
                  ? `当前有 ${activeTasks.length} 个任务进行中，${activeProjects.length} 个活跃项目。`
                  : "暂无进行中的任务。"}
                {pendingDecisions.length > 0
                  ? ` ${pendingDecisions.length} 个决策待你审批。`
                  : ""}
                {atRiskTasks.length > 0
                  ? ` 注意：${atRiskTasks.length} 个事项存在风险，建议优先处理。`
                  : " 整体经营状态良好，无高风险事项。"}
                {notifications.length > 0
                  ? ` 另有 ${notifications.length} 条未读通知。`
                  : ""}
              </p>
            )}
            <div className="flex items-center gap-3 mt-3">
              <Link
                href="/chat"
                className="inline-flex items-center gap-1 text-xs text-brand-300 hover:text-white transition-colors"
              >
                与 CEO Agent 对话 <ChevronRight className="h-3 w-3" />
              </Link>
              {todayBriefing?.created_at && (
                <span className="text-[10px] text-brand-400">
                  生成于 {new Date(todayBriefing.created_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
                </span>
              )}
            </div>
          </div>

          {/* Pending Decisions */}
          {pendingDecisions.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold">待决策事项</h2>
                <Link href="/decisions" className="text-xs text-brand-600 hover:underline">查看全部</Link>
              </div>
              <div className="space-y-2">
                {pendingDecisions.slice(0, 3).map((d) => (
                  <Link
                    key={d.id}
                    href="/decisions"
                    className="flex items-start gap-3 p-4 rounded-xl bg-[hsl(var(--card))] border hover:border-brand-300 transition-colors"
                  >
                    <div className="w-8 h-8 rounded-full bg-gold-100 dark:bg-gold-900/30 flex items-center justify-center shrink-0 mt-0.5">
                      <GitBranch className="h-4 w-4 text-gold-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium truncate">{d.title}</p>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full shrink-0 ${
                          d.risk_level === "high" ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" :
                          "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                        }`}>{d.risk_level === "high" ? "紧急" : "重要"}</span>
                      </div>
                      {d.problem_statement && (
                        <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5 line-clamp-1">{d.problem_statement}</p>
                      )}
                    </div>
                    <ChevronRight className="h-4 w-4 text-[hsl(var(--muted-foreground))] shrink-0 mt-1" />
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Active Tasks */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold">进行中的任务</h2>
              <Link href="/tasks" className="text-xs text-brand-600 hover:underline">查看全部</Link>
            </div>
            <div className="space-y-2">
              {activeTasks.length === 0 && tasks.filter(t => t.status === "pending").length === 0 ? (
                <p className="text-sm text-[hsl(var(--muted-foreground))] text-center py-6">暂无任务</p>
              ) : (
                [...activeTasks, ...tasks.filter(t => t.status === "pending")].slice(0, 5).map((task) => (
                  <Link
                    key={task.id}
                    href="/tasks"
                    className="flex items-center gap-3 p-3 rounded-xl bg-[hsl(var(--card))] border hover:border-brand-300 transition-colors text-sm"
                  >
                    {task.status === "in_progress" ? (
                      <Clock className="h-4 w-4 text-blue-500 shrink-0" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 text-gray-400 shrink-0" />
                    )}
                    <span className="flex-1 truncate font-medium">{task.title}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full shrink-0 ${
                      task.priority === "high" || task.priority === "urgent"
                        ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                        : task.priority === "medium"
                        ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                        : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                    }`}>{task.priority}</span>
                    {task.due_date && (
                      <span className="text-xs text-[hsl(var(--muted-foreground))] shrink-0">{task.due_date}</span>
                    )}
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right sidebar */}
        <div className="space-y-4">
          {/* Today Focus */}
          <div className="p-4 rounded-xl bg-[hsl(var(--card))] border">
            <h3 className="text-sm font-semibold mb-3">今日关注</h3>
            <div className="space-y-3">
              <Link href="/heartbeat" className="flex items-center justify-between text-sm hover:text-brand-600 transition-colors">
                <span className="text-[hsl(var(--muted-foreground))]">风险事项</span>
                <span className="font-medium">{atRiskTasks.length} 项</span>
              </Link>
              <div className="h-px bg-[hsl(var(--border))]" />
              <Link href="/decisions" className="flex items-center justify-between text-sm hover:text-brand-600 transition-colors">
                <span className="text-[hsl(var(--muted-foreground))]">待决策事项</span>
                <span className="font-medium">{pendingDecisions.length} 条</span>
              </Link>
              <div className="h-px bg-[hsl(var(--border))]" />
              <Link href="/projects" className="flex items-center justify-between text-sm hover:text-brand-600 transition-colors">
                <span className="text-[hsl(var(--muted-foreground))]">活跃项目</span>
                <span className="font-medium">{activeProjects.length} 个</span>
              </Link>
              <div className="h-px bg-[hsl(var(--border))]" />
              <Link href="/memories" className="flex items-center justify-between text-sm hover:text-brand-600 transition-colors">
                <span className="text-[hsl(var(--muted-foreground))]">长期记忆</span>
                <span className="font-medium">{confirmedMemories.length} 条</span>
              </Link>
            </div>
          </div>

          {/* Active Projects */}
          {activeProjects.length > 0 && (
            <div className="p-4 rounded-xl bg-[hsl(var(--card))] border">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold">项目进度</h3>
                <Link href="/projects" className="text-xs text-brand-600 hover:underline">全部</Link>
              </div>
              <div className="space-y-3">
                {activeProjects.slice(0, 4).map((p) => (
                  <div key={p.id}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="truncate font-medium">{p.name}</span>
                      <span className="text-xs text-[hsl(var(--muted-foreground))] shrink-0 ml-2">{p.progress_percent}%</span>
                    </div>
                    <div className="h-1.5 bg-[hsl(var(--muted))] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-brand-500 rounded-full transition-all"
                        style={{ width: `${p.progress_percent}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Notifications */}
          {notifications.length > 0 && (
            <div className="p-4 rounded-xl bg-[hsl(var(--card))] border">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold">最新通知</h3>
                <Link href="/notifications" className="text-xs text-brand-600 hover:underline">全部</Link>
              </div>
              <div className="space-y-2">
                {notifications.slice(0, 3).map((n) => (
                  <div key={n.id} className="text-sm">
                    <p className="font-medium text-xs">{n.title}</p>
                    {n.content && (
                      <p className="text-xs text-[hsl(var(--muted-foreground))] line-clamp-1">{n.content}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
