"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/layout/page-header";
import { Brain, Check, X, Search, RefreshCw, Heart } from "lucide-react";
import type { Memory } from "@/types";

const memoryTypeLabels: Record<string, { label: string; color: string }> = {
  founder_profile: { label: "创始人画像", color: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" },
  preference: { label: "个人偏好", color: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400" },
  company_fact: { label: "公司事实", color: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" },
  employee_fact: { label: "员工信息", color: "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400" },
  product_fact: { label: "产品信息", color: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400" },
  supplier_fact: { label: "供应商", color: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" },
  project_fact: { label: "项目事实", color: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400" },
  decision: { label: "决策历史", color: "bg-gold-100 text-gold-700 dark:bg-gold-900/30 dark:text-gold-400" },
  lesson: { label: "经验教训", color: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" },
  risk: { label: "风险", color: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" },
  strategy: { label: "战略", color: "bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400" },
  process: { label: "流程", color: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400" },
  relationship: { label: "关系", color: "bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400" },
  temporary_context: { label: "临时上下文", color: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400" },
};

const typeFilters = [
  { value: "", label: "全部" },
  { value: "decision", label: "决策历史" },
  { value: "preference", label: "个人偏好" },
  { value: "company_fact", label: "重要上下文" },
  { value: "strategy", label: "战略" },
];

export default function MemoriesPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: memories = [] } = useQuery({
    queryKey: ["memories", statusFilter],
    queryFn: () => api.get<Memory[]>(`/api/memories${statusFilter ? `?status_filter=${statusFilter}` : ""}`),
  });

  const confirm = useMutation({
    mutationFn: (id: string) => api.post(`/api/memories/${id}/confirm`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["memories"] }),
  });

  const reject = useMutation({
    mutationFn: (id: string) => api.post(`/api/memories/${id}/reject`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["memories"] }),
  });

  const filtered = memories.filter(
    (m) =>
      (!searchQuery || m.title.includes(searchQuery) || m.content.includes(searchQuery)) &&
      (!typeFilter || m.memory_type === typeFilter)
  );

  const proposed = filtered.filter((m) => m.status === "proposed");
  const confirmed = filtered.filter((m) => m.status === "confirmed");
  const allConfirmed = memories.filter(m => m.status === "confirmed");

  const avgImportance = allConfirmed.length > 0
    ? Math.round(allConfirmed.reduce((sum, m) => sum + m.importance_score, 0) / allConfirmed.length * 100)
    : 0;
  const avgConfidence = allConfirmed.length > 0
    ? Math.round(allConfirmed.reduce((sum, m) => sum + m.confidence_score, 0) / allConfirmed.length * 100)
    : 0;
  const healthScore = allConfirmed.length > 0
    ? Math.round((avgImportance + avgConfidence) / 2)
    : 0;

  const typeCounts = allConfirmed.reduce<Record<string, number>>((acc, m) => {
    acc[m.memory_type] = (acc[m.memory_type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="max-w-6xl mx-auto px-6 py-6">
      <PageHeader
        tag="Long-Term Memory"
        title="长期记忆库"
        description="CEO Agent 的持久化知识库，记录你的偏好、决策历史和重要上下文。"
        action={
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))]">
            <RefreshCw className="h-3.5 w-3.5" /> 更新数据
          </button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-[hsl(var(--muted-foreground))]" />
              <input
                placeholder="搜索记忆..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <div className="flex gap-2 flex-wrap">
            {[
              { value: "", label: "全部" },
              { value: "proposed", label: "待确认" },
              { value: "confirmed", label: "已确认" },
            ].map((f) => (
              <button
                key={f.value}
                onClick={() => setStatusFilter(f.value)}
                className={cn(
                  "px-3 py-1 rounded-full text-xs transition-colors",
                  statusFilter === f.value ? "bg-brand-700 text-white" : "bg-[hsl(var(--muted))]"
                )}
              >
                {f.label}
              </button>
            ))}
            <div className="w-px bg-[hsl(var(--border))]" />
            {typeFilters.map((f) => (
              <button
                key={f.value}
                onClick={() => setTypeFilter(typeFilter === f.value ? "" : f.value)}
                className={cn(
                  "px-3 py-1 rounded-full text-xs transition-colors",
                  typeFilter === f.value ? "bg-brand-700 text-white" : "bg-[hsl(var(--muted))]"
                )}
              >
                {f.label}
              </button>
            ))}
          </div>

          {proposed.length > 0 && (
            <div className="space-y-2">
              <h2 className="text-sm font-semibold text-orange-600">待确认 ({proposed.length})</h2>
              {proposed.map((memory) => (
                <div key={memory.id} className="p-4 rounded-xl bg-orange-50 dark:bg-orange-900/10 border border-orange-200 dark:border-orange-800/30">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center shrink-0">
                      <Brain className="h-4 w-4 text-orange-600" />
                    </div>
                    <div className="flex-1">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        memoryTypeLabels[memory.memory_type]?.color || "bg-gray-100 text-gray-600"
                      }`}>
                        {memoryTypeLabels[memory.memory_type]?.label || memory.memory_type}
                      </span>
                      <h3 className="font-medium mt-1 text-sm">{memory.title}</h3>
                      <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">{memory.content}</p>
                      <div className="flex gap-2 mt-3">
                        <button
                          onClick={() => confirm.mutate(memory.id)}
                          className="flex items-center gap-1 px-3 py-1 rounded-lg bg-brand-700 text-white text-xs hover:bg-brand-800"
                        >
                          <Check className="h-3 w-3" /> 确认
                        </button>
                        <button
                          onClick={() => reject.mutate(memory.id)}
                          className="flex items-center gap-1 px-3 py-1 rounded-lg border text-xs hover:bg-[hsl(var(--muted))]"
                        >
                          <X className="h-3 w-3" /> 拒绝
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="space-y-2">
            {confirmed.length > 0 && <h2 className="text-sm font-semibold">已确认的记忆 ({confirmed.length})</h2>}
            {confirmed.map((memory) => (
              <div key={memory.id} className="p-4 rounded-xl bg-[hsl(var(--card))] border">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center shrink-0">
                    <Brain className="h-4 w-4 text-brand-600" />
                  </div>
                  <div className="flex-1">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      memoryTypeLabels[memory.memory_type]?.color || "bg-gray-100 text-gray-600"
                    }`}>
                      {memoryTypeLabels[memory.memory_type]?.label || memory.memory_type}
                    </span>
                    <h3 className="font-medium mt-1 text-sm">{memory.title}</h3>
                    <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">{memory.content}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-[hsl(var(--muted-foreground))]">
                      <span>重要性 {(memory.importance_score * 100).toFixed(0)}%</span>
                      <span>置信度 {(memory.confidence_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {filtered.length === 0 && (
              <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-12">暂无记忆</p>
            )}
          </div>
        </div>

        {/* Right Panel */}
        <div className="space-y-4">
          {/* Memory Health */}
          <div className="p-5 rounded-xl bg-brand-900 text-white dark:bg-brand-950">
            <div className="flex items-center gap-2 mb-4">
              <Heart className="h-5 w-5 text-brand-300" />
              <span className="text-sm font-semibold text-brand-200">记忆健康度</span>
            </div>
            <div className="flex items-end gap-2 mb-3">
              <span className="text-4xl font-bold">{healthScore || "—"}</span>
              {healthScore > 0 && <span className="text-sm text-brand-300 mb-1">/ 100</span>}
            </div>
            <div className="h-2 bg-brand-800 rounded-full overflow-hidden mb-3">
              <div
                className="h-full bg-brand-400 rounded-full transition-all"
                style={{ width: `${healthScore}%` }}
              />
            </div>
            <p className="text-xs text-brand-300">
              共 {allConfirmed.length} 条已确认记忆
            </p>
          </div>

          {/* Memory Distribution */}
          <div className="p-4 rounded-xl bg-[hsl(var(--card))] border">
            <h3 className="text-sm font-semibold mb-3">记忆分布</h3>
            <div className="space-y-2">
              {Object.entries(typeCounts)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 8)
                .map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between text-sm">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      memoryTypeLabels[type]?.color || "bg-gray-100 text-gray-600"
                    }`}>
                      {memoryTypeLabels[type]?.label || type}
                    </span>
                    <span className="text-xs text-[hsl(var(--muted-foreground))]">{count} 条</span>
                  </div>
                ))}
              {Object.keys(typeCounts).length === 0 && (
                <p className="text-xs text-[hsl(var(--muted-foreground))] text-center py-2">暂无数据</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
