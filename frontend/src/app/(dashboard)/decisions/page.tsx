"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { GitBranch, Check, X, Eye } from "lucide-react";
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

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      <h1 className="text-xl font-bold">决策中心</h1>

      {selected && (
        <div className="p-4 rounded-xl bg-[hsl(var(--card))] border space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">{selected.title}</h3>
            <button onClick={() => setSelectedId(null)} className="text-sm text-[hsl(var(--muted-foreground))]">关闭</button>
          </div>
          {selected.problem_statement && (
            <div><p className="text-xs font-medium text-[hsl(var(--muted-foreground))]">问题</p><p className="text-sm">{selected.problem_statement}</p></div>
          )}
          {selected.context && (
            <div><p className="text-xs font-medium text-[hsl(var(--muted-foreground))]">背景</p><p className="text-sm">{selected.context}</p></div>
          )}
          {selected.rationale && (
            <div><p className="text-xs font-medium text-[hsl(var(--muted-foreground))]">理由</p><p className="text-sm">{selected.rationale}</p></div>
          )}
          {selected.decision_status === "proposed" && (
            <div className="flex gap-2">
              <button
                onClick={() => approve.mutate(selected.id)}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-green-600 text-white text-sm"
              >
                <Check className="h-3.5 w-3.5" /> 批准
              </button>
              <button className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-600 text-white text-sm">
                <X className="h-3.5 w-3.5" /> 拒绝
              </button>
            </div>
          )}
        </div>
      )}

      <div className="space-y-2">
        {decisions.map((d) => (
          <button
            key={d.id}
            onClick={() => setSelectedId(d.id)}
            className="w-full text-left p-3 rounded-xl bg-[hsl(var(--card))] border hover:border-brand-300 transition-colors"
          >
            <div className="flex items-start gap-3">
              <GitBranch className="h-5 w-5 text-brand-500 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium">{d.title}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                  <span className={`px-1.5 py-0.5 rounded ${
                    d.decision_status === "approved" ? "bg-green-100 text-green-700" :
                    d.decision_status === "proposed" ? "bg-yellow-100 text-yellow-700" :
                    "bg-gray-100 text-gray-600"
                  }`}>{d.decision_status}</span>
                  <span>{d.risk_level}</span>
                </div>
              </div>
            </div>
          </button>
        ))}
        {decisions.length === 0 && (
          <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-8">暂无决策记录</p>
        )}
      </div>
    </div>
  );
}
