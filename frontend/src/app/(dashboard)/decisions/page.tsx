"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { GitBranch, Check, X, ChevronRight, Sparkles, RefreshCw } from "lucide-react";
import type { Decision } from "@/types";

export default function DecisionsPage() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: decisions = [] } = useQuery({
    queryKey: ["decisions"],
    queryFn: () => api.get<Decision[]>("/api/decisions"),
  });

  const approve = useMutation({
    mutationFn: (id: string) => api.post(`/api/decisions/${id}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["decisions"] }),
  });

  const selected = decisions.find((d) => d.id === selectedId);
  const proposed = decisions.filter(d => d.decision_status === "proposed");
  const approved = decisions.filter(d => d.decision_status === "approved");
  const readinessScore = proposed.length > 0
    ? Math.round((approved.length / (approved.length + proposed.length)) * 100)
    : 100;

  return (
    <div className="max-w-6xl mx-auto px-6 py-6">
      <PageHeader
        tag="Decision Queue"
        title="待决策事项列表"
        description="聚焦需要 CEO 拍板的事项，并持续记录决策上下文。"
        action={
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))]">
            <RefreshCw className="h-3.5 w-3.5" /> 更新数据
          </button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Decision List */}
        <div className="lg:col-span-2 space-y-3">
          {decisions.length === 0 && (
            <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-12">暂无决策记录</p>
          )}
          {decisions.map((d) => (
            <button
              key={d.id}
              onClick={() => setSelectedId(d.id)}
              className="w-full text-left p-4 rounded-xl bg-[hsl(var(--card))] border hover:border-brand-300 transition-colors"
            >
              <div className="flex items-start gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                  d.decision_status === "approved"
                    ? "bg-green-100 dark:bg-green-900/30"
                    : "bg-gold-100 dark:bg-gold-900/30"
                }`}>
                  {d.decision_status === "approved" ? (
                    <Check className="h-4 w-4 text-green-600" />
                  ) : (
                    <GitBranch className="h-4 w-4 text-gold-600" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium">{d.title}</p>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full shrink-0 ${
                      d.risk_level === "high" ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" :
                      d.decision_status === "proposed" ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" :
                      "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                    }`}>
                      {d.risk_level === "high" ? "紧急" : d.decision_status === "proposed" ? "重要" : "常规"}
                    </span>
                  </div>
                  {d.problem_statement && (
                    <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1 line-clamp-1">{d.problem_statement}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {d.decision_status === "proposed" && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        approve.mutate(d.id);
                      }}
                      className="px-3 py-1 rounded-lg bg-brand-700 text-white text-xs hover:bg-brand-800"
                    >
                      标记已决策
                    </button>
                  )}
                  <ChevronRight className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Right Panel */}
        <div className="space-y-4">
          {/* Decision Readiness */}
          <div className="p-5 rounded-xl bg-brand-900 text-white dark:bg-brand-950">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-5 w-5 text-brand-300" />
              <span className="text-sm font-semibold text-brand-200">决策准备度</span>
            </div>
            <div className="flex items-end gap-3 mb-2">
              <span className="text-4xl font-bold">{readinessScore}</span>
              <span className="text-sm text-brand-300 mb-1">/ 100</span>
            </div>
            <div className="h-2 bg-brand-800 rounded-full overflow-hidden mb-3">
              <div
                className="h-full bg-brand-400 rounded-full transition-all"
                style={{ width: `${readinessScore}%` }}
              />
            </div>
            <p className="text-xs text-brand-300">
              {proposed.length > 0
                ? `当前 ${proposed.length} 个事项待决策`
                : "所有决策事项已处理完毕"}
            </p>
          </div>

          {/* Selected Detail */}
          {selected && (
            <div className="p-4 rounded-xl bg-[hsl(var(--card))] border space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold">详情</h3>
                <button onClick={() => setSelectedId(null)} className="text-xs text-[hsl(var(--muted-foreground))]">
                  <X className="h-4 w-4" />
                </button>
              </div>
              <h4 className="font-medium text-sm">{selected.title}</h4>
              {selected.problem_statement && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))] mb-0.5">问题</p>
                  <p className="text-sm">{selected.problem_statement}</p>
                </div>
              )}
              {selected.context && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))] mb-0.5">背景</p>
                  <p className="text-sm">{selected.context}</p>
                </div>
              )}
              {selected.rationale && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))] mb-0.5">理由</p>
                  <p className="text-sm">{selected.rationale}</p>
                </div>
              )}
              {selected.decision_status === "proposed" && (
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => approve.mutate(selected.id)}
                    className="flex-1 flex items-center justify-center gap-1 px-3 py-2 rounded-lg bg-brand-700 text-white text-sm hover:bg-brand-800"
                  >
                    <Check className="h-3.5 w-3.5" /> 批准
                  </button>
                  <button className="flex-1 flex items-center justify-center gap-1 px-3 py-2 rounded-lg border text-sm hover:bg-[hsl(var(--muted))]">
                    添加备注
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
