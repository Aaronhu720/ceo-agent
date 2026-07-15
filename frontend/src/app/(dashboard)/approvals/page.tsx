"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import { PageHeader } from "@/components/layout/page-header";
import { ShieldCheck, Check, X } from "lucide-react";

interface Approval {
  id: string;
  action_type: string;
  action_description: string | null;
  risk_level: string;
  status: string;
  created_at: string;
}

export default function ApprovalsPage() {
  const queryClient = useQueryClient();

  const { data: approvals = [] } = useQuery({
    queryKey: ["approvals"],
    queryFn: () => api.get<Approval[]>("/api/approvals"),
  });

  const approve = useMutation({
    mutationFn: (id: string) => api.post(`/api/approvals/${id}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["approvals"] }),
  });

  const reject = useMutation({
    mutationFn: (id: string) => api.post(`/api/approvals/${id}/reject`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["approvals"] }),
  });

  return (
    <div className="max-w-4xl mx-auto px-6 py-6 space-y-4">
      <PageHeader tag="Approvals" title="审批中心" description="管理 Agent 提交的操作审批请求。" />

      <div className="space-y-2">
        {approvals.map((a) => (
          <div key={a.id} className="p-4 rounded-xl bg-[hsl(var(--card))] border">
            <div className="flex items-start gap-3">
              <ShieldCheck className={`h-5 w-5 mt-0.5 shrink-0 ${
                a.status === "approved" ? "text-green-500" :
                a.status === "rejected" ? "text-red-500" :
                "text-yellow-500"
              }`} />
              <div className="flex-1">
                <p className="text-sm font-medium">{a.action_type}</p>
                {a.action_description && (
                  <p className="text-sm text-[hsl(var(--muted-foreground))] mt-0.5">{a.action_description}</p>
                )}
                <div className="flex items-center gap-2 mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                  <span className={`px-1.5 py-0.5 rounded ${
                    a.risk_level === "high" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"
                  }`}>{a.risk_level}</span>
                  <span>{formatRelativeTime(a.created_at)}</span>
                </div>
                {a.status === "pending" && (
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => approve.mutate(a.id)}
                      className="flex items-center gap-1 px-3 py-1 rounded-lg bg-green-600 text-white text-xs"
                    >
                      <Check className="h-3 w-3" /> 批准
                    </button>
                    <button
                      onClick={() => reject.mutate(a.id)}
                      className="flex items-center gap-1 px-3 py-1 rounded-lg bg-red-600 text-white text-xs"
                    >
                      <X className="h-3 w-3" /> 拒绝
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {approvals.length === 0 && (
          <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-8">暂无审批</p>
        )}
      </div>
    </div>
  );
}
