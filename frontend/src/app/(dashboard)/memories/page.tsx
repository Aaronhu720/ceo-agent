"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Brain, Check, X, Search } from "lucide-react";
import type { Memory } from "@/types";

const memoryTypeLabels: Record<string, string> = {
  founder_profile: "创始人画像",
  preference: "偏好",
  company_fact: "公司事实",
  employee_fact: "员工信息",
  product_fact: "产品信息",
  supplier_fact: "供应商",
  project_fact: "项目事实",
  decision: "决策",
  lesson: "经验教训",
  risk: "风险",
  strategy: "战略",
  process: "流程",
  relationship: "关系",
  temporary_context: "临时上下文",
};

export default function MemoriesPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
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
    (m) => !searchQuery || m.title.includes(searchQuery) || m.content.includes(searchQuery)
  );

  const proposed = filtered.filter((m) => m.status === "proposed");
  const confirmed = filtered.filter((m) => m.status === "confirmed");

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      <h1 className="text-xl font-bold">记忆中心</h1>

      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-[hsl(var(--muted-foreground))]" />
        <input
          placeholder="搜索记忆..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-9 pr-4 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </div>

      <div className="flex gap-2">
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
              statusFilter === f.value ? "bg-brand-600 text-white" : "bg-[hsl(var(--muted))]"
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
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="text-xs px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400">
                    {memoryTypeLabels[memory.memory_type] || memory.memory_type}
                  </span>
                  <h3 className="font-medium mt-1 text-sm">{memory.title}</h3>
                  <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">{memory.content}</p>
                </div>
              </div>
              <div className="flex gap-2 mt-3">
                <button
                  onClick={() => confirm.mutate(memory.id)}
                  className="flex items-center gap-1 px-3 py-1 rounded-lg bg-green-600 text-white text-xs"
                >
                  <Check className="h-3 w-3" /> 确认
                </button>
                <button
                  onClick={() => reject.mutate(memory.id)}
                  className="flex items-center gap-1 px-3 py-1 rounded-lg bg-red-600 text-white text-xs"
                >
                  <X className="h-3 w-3" /> 拒绝
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-2">
        {confirmed.length > 0 && <h2 className="text-sm font-semibold">已确认的记忆</h2>}
        {confirmed.map((memory) => (
          <div key={memory.id} className="p-3 rounded-xl bg-[hsl(var(--card))] border text-sm">
            <div className="flex items-start gap-2">
              <Brain className="h-4 w-4 text-purple-500 mt-0.5 shrink-0" />
              <div>
                <span className="text-xs px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                  {memoryTypeLabels[memory.memory_type] || memory.memory_type}
                </span>
                <h3 className="font-medium mt-1">{memory.title}</h3>
                <p className="text-[hsl(var(--muted-foreground))] mt-0.5">{memory.content}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                  <span>重要性: {(memory.importance_score * 100).toFixed(0)}%</span>
                  <span>置信度: {(memory.confidence_score * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-8">暂无记忆</p>
        )}
      </div>
    </div>
  );
}
