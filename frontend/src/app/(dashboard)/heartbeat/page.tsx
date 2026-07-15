"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { AlertTriangle, Shield, RefreshCw, ChevronRight } from "lucide-react";
import type { Task } from "@/types";

interface HeartbeatRule {
  id: string;
  name: string;
  description: string | null;
  frequency_type: string;
  cron_expression: string | null;
  check_type: string;
  priority: string;
  enabled: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
}

export default function HeartbeatPage() {
  const { data: rules = [] } = useQuery({
    queryKey: ["heartbeat-rules"],
    queryFn: () => api.get<HeartbeatRule[]>("/api/heartbeat-rules"),
  });

  const { data: tasks = [] } = useQuery({
    queryKey: ["tasks-risks"],
    queryFn: () => api.get<Task[]>("/api/tasks"),
  });

  const riskTasks = tasks.filter(t => t.risk_level === "high" || t.status === "at_risk");
  const mediumRisks = tasks.filter(t => t.risk_level === "medium");
  const riskIndex = riskTasks.length === 0 && mediumRisks.length === 0
    ? 95
    : Math.max(0, 100 - riskTasks.length * 15 - mediumRisks.length * 5);

  return (
    <div className="max-w-6xl mx-auto px-6 py-6">
      <PageHeader
        tag="Risk Intelligence"
        title="风险雷达模块"
        description="识别风险敞口、责任人和跟进状态，避免重要信号被淹没。"
        action={
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))]">
            <RefreshCw className="h-3.5 w-3.5" /> 更新数据
          </button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Radar Visualization */}
        <div>
          <div className="p-6 rounded-2xl bg-brand-900 dark:bg-brand-950 text-white">
            <div className="flex flex-col items-center mb-4">
              <div className="relative w-40 h-40 flex items-center justify-center">
                <svg viewBox="0 0 160 160" className="w-full h-full">
                  <circle cx="80" cy="80" r="70" fill="none" stroke="hsl(153,30%,25%)" strokeWidth="2" />
                  <circle cx="80" cy="80" r="50" fill="none" stroke="hsl(153,30%,25%)" strokeWidth="1" />
                  <circle cx="80" cy="80" r="30" fill="none" stroke="hsl(153,30%,25%)" strokeWidth="1" />
                  {riskTasks.map((_, i) => {
                    const angle = (i / Math.max(riskTasks.length, 1)) * Math.PI * 2 - Math.PI / 2;
                    const r = 25 + Math.random() * 20;
                    return (
                      <circle
                        key={i}
                        cx={80 + Math.cos(angle) * r}
                        cy={80 + Math.sin(angle) * r}
                        r="5"
                        fill="#ef4444"
                        opacity="0.8"
                      />
                    );
                  })}
                  {mediumRisks.map((_, i) => {
                    const angle = (i / Math.max(mediumRisks.length, 1)) * Math.PI * 2;
                    const r = 40 + Math.random() * 15;
                    return (
                      <circle
                        key={`m-${i}`}
                        cx={80 + Math.cos(angle) * r}
                        cy={80 + Math.sin(angle) * r}
                        r="4"
                        fill="#eab308"
                        opacity="0.7"
                      />
                    );
                  })}
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-bold">{riskIndex}</span>
                  <span className="text-[10px] uppercase tracking-wider text-brand-300">Risk Index</span>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center p-2 rounded-lg bg-brand-800/50">
                <p className="text-lg font-bold">{riskTasks.length}</p>
                <p className="text-[10px] text-brand-300">高风险</p>
              </div>
              <div className="text-center p-2 rounded-lg bg-brand-800/50">
                <p className="text-lg font-bold">{mediumRisks.length}</p>
                <p className="text-[10px] text-brand-300">中风险</p>
              </div>
            </div>
          </div>
        </div>

        {/* Risk Items */}
        <div className="lg:col-span-2 space-y-3">
          {riskTasks.length === 0 && mediumRisks.length === 0 && rules.length === 0 && (
            <div className="text-center py-12">
              <Shield className="h-12 w-12 text-brand-300 mx-auto mb-3" />
              <p className="text-sm text-[hsl(var(--muted-foreground))]">暂无风险事项，系统运行正常</p>
            </div>
          )}

          {riskTasks.map((task) => (
            <div key={task.id} className="p-4 rounded-xl bg-[hsl(var(--card))] border hover:border-brand-300 transition-colors">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center shrink-0 mt-0.5">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium">{task.title}</p>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
                      高风险
                    </span>
                  </div>
                  {task.description && (
                    <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">{task.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-[hsl(var(--muted))]">
                    等级：高
                  </span>
                  <span className="text-xs text-brand-600 flex items-center gap-0.5">
                    跟进中 <ChevronRight className="h-3 w-3" />
                  </span>
                </div>
              </div>
            </div>
          ))}

          {mediumRisks.map((task) => (
            <div key={task.id} className="p-4 rounded-xl bg-[hsl(var(--card))] border hover:border-brand-300 transition-colors">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center shrink-0 mt-0.5">
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium">{task.title}</p>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
                      中风险
                    </span>
                  </div>
                  {task.description && (
                    <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">{task.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-[hsl(var(--muted))]">
                    等级：中
                  </span>
                </div>
              </div>
            </div>
          ))}

          {rules.length > 0 && (
            <>
              <h3 className="text-sm font-semibold mt-4">自动巡检规则</h3>
              {rules.map((rule) => (
                <div key={rule.id} className="p-4 rounded-xl bg-[hsl(var(--card))] border">
                  <div className="flex items-center gap-3">
                    <Shield className={`h-5 w-5 ${rule.enabled ? "text-brand-500" : "text-gray-400"}`} />
                    <div className="flex-1">
                      <h4 className="text-sm font-medium">{rule.name}</h4>
                      {rule.description && (
                        <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5">{rule.description}</p>
                      )}
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                      rule.enabled ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : "bg-gray-100 text-gray-500"
                    }`}>
                      {rule.enabled ? "启用" : "停用"}
                    </span>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
