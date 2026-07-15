"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Plus, FolderKanban, X, ChevronRight } from "lucide-react";
import type { Project } from "@/types";

export default function ProjectsPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", objective: "", priority: "medium" });

  const { data: projects = [] } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.get<Project[]>("/api/projects"),
  });

  const createProject = useMutation({
    mutationFn: (data: typeof form) => api.post("/api/projects", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setShowCreate(false);
      setForm({ name: "", description: "", objective: "", priority: "medium" });
    },
  });

  return (
    <div className="max-w-6xl mx-auto px-6 py-6">
      <PageHeader
        tag="Project Portfolio"
        title="项目管理"
        description="查看和管理所有项目的进度与状态。"
        action={
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-700 text-white text-sm hover:bg-brand-800 transition-colors"
          >
            <Plus className="h-4 w-4" /> 新建项目
          </button>
        }
      />

      {showCreate && (
        <div className="mb-6 p-4 rounded-xl bg-[hsl(var(--card))] border space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">新建项目</h3>
            <button onClick={() => setShowCreate(false)} className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]">
              <X className="h-4 w-4" />
            </button>
          </div>
          <input
            placeholder="项目名称"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full px-3 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <textarea
            placeholder="项目描述"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="w-full px-3 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            rows={2}
          />
          <input
            placeholder="目标"
            value={form.objective}
            onChange={(e) => setForm({ ...form, objective: e.target.value })}
            className="w-full px-3 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowCreate(false)} className="px-3 py-1.5 text-sm rounded-lg hover:bg-[hsl(var(--muted))]">取消</button>
            <button
              onClick={() => createProject.mutate(form)}
              disabled={!form.name}
              className="px-3 py-1.5 text-sm rounded-lg bg-brand-700 text-white hover:bg-brand-800 disabled:opacity-50"
            >创建</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map((project) => (
          <div key={project.id} className="p-5 rounded-xl bg-[hsl(var(--card))] border hover:border-brand-300 transition-colors">
            <div className="flex items-start justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center">
                <FolderKanban className="h-5 w-5 text-brand-700 dark:text-brand-400" />
              </div>
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                project.status === "active" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" :
                project.status === "completed" ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" :
                "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
              }`}>{project.status}</span>
            </div>

            <h3 className="font-semibold text-sm">{project.name}</h3>
            {project.description && (
              <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1 line-clamp-2">{project.description}</p>
            )}

            <div className="mt-4">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-[hsl(var(--muted-foreground))]">进度</span>
                <span className="font-medium">{project.progress_percent}%</span>
              </div>
              <div className="h-1.5 bg-[hsl(var(--muted))] rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand-500 rounded-full transition-all"
                  style={{ width: `${project.progress_percent}%` }}
                />
              </div>
            </div>

            <div className="flex items-center justify-between mt-3">
              <div className="flex items-center gap-2 text-xs text-[hsl(var(--muted-foreground))]">
                {project.target_date && <span>{project.target_date}</span>}
                {project.risk_level === "high" && (
                  <span className="px-1 py-0.5 rounded bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
                    高风险
                  </span>
                )}
              </div>
              <span className="text-xs text-brand-600 flex items-center gap-0.5">
                详情 <ChevronRight className="h-3 w-3" />
              </span>
            </div>
          </div>
        ))}
        {projects.length === 0 && (
          <div className="col-span-3 text-center text-sm text-[hsl(var(--muted-foreground))] py-12">暂无项目</div>
        )}
      </div>
    </div>
  );
}
