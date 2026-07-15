"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Plus, FolderKanban } from "lucide-react";
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
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">项目</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm hover:bg-brand-700"
        >
          <Plus className="h-4 w-4" /> 新建
        </button>
      </div>

      {showCreate && (
        <div className="p-4 rounded-xl bg-[hsl(var(--card))] border space-y-3">
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
              className="px-3 py-1.5 text-sm rounded-lg bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50"
            >创建</button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {projects.map((project) => (
          <div key={project.id} className="p-4 rounded-xl bg-[hsl(var(--card))] border">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center shrink-0">
                <FolderKanban className="h-5 w-5 text-brand-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium">{project.name}</h3>
                {project.description && (
                  <p className="text-sm text-[hsl(var(--muted-foreground))] mt-0.5">{project.description}</p>
                )}
                <div className="flex items-center gap-3 mt-2">
                  <div className="flex-1 h-2 bg-[hsl(var(--muted))] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-brand-500 rounded-full transition-all"
                      style={{ width: `${project.progress_percent}%` }}
                    />
                  </div>
                  <span className="text-xs text-[hsl(var(--muted-foreground))] whitespace-nowrap">
                    {project.progress_percent}%
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-2 text-xs text-[hsl(var(--muted-foreground))]">
                  <span className={`px-1.5 py-0.5 rounded ${
                    project.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
                  }`}>{project.status}</span>
                  {project.target_date && <span>目标: {project.target_date}</span>}
                  <span className={`px-1.5 py-0.5 rounded ${
                    project.risk_level === "high" ? "bg-red-100 text-red-700" : ""
                  }`}>{project.risk_level}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
        {projects.length === 0 && (
          <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-8">暂无项目</p>
        )}
      </div>
    </div>
  );
}
