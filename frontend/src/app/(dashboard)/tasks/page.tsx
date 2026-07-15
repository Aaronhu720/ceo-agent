"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/layout/page-header";
import { Plus, CheckCircle2, Circle, Clock, AlertTriangle, ChevronRight, X } from "lucide-react";
import type { Task } from "@/types";

const kanbanColumns = [
  { status: "pending", label: "待启动", color: "bg-gray-400" },
  { status: "in_progress", label: "进行中", color: "bg-yellow-500" },
  { status: "at_risk", label: "有风险", color: "bg-red-500" },
  { status: "completed", label: "已完成", color: "bg-green-500" },
];

export default function TasksPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newTask, setNewTask] = useState({ title: "", description: "", priority: "medium", due_date: "" });

  const { data: tasks = [] } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => api.get<Task[]>("/api/tasks"),
  });

  const createTask = useMutation({
    mutationFn: (data: typeof newTask) => api.post("/api/tasks", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      setShowCreate(false);
      setNewTask({ title: "", description: "", priority: "medium", due_date: "" });
    },
  });

  const updateTask = useMutation({
    mutationFn: ({ id, ...data }: { id: string; status?: string }) =>
      api.patch(`/api/tasks/${id}`, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
  });

  const getNextStatus = (current: string) => {
    const flow: Record<string, string> = {
      pending: "in_progress",
      in_progress: "completed",
      at_risk: "in_progress",
      completed: "pending",
    };
    return flow[current] || "pending";
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-6">
      <PageHeader
        tag="Execution Portfolio"
        title="任务与项目看板"
        description="查看跨部门关键项目进度、状态流转与负责人。"
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
            <h3 className="text-sm font-semibold">新建任务</h3>
            <button onClick={() => setShowCreate(false)} className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]">
              <X className="h-4 w-4" />
            </button>
          </div>
          <input
            placeholder="任务标题"
            value={newTask.title}
            onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
            className="w-full px-3 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <textarea
            placeholder="描述（可选）"
            value={newTask.description}
            onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
            className="w-full px-3 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            rows={2}
          />
          <div className="flex gap-2">
            <select
              value={newTask.priority}
              onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
              className="px-3 py-2 rounded-lg border bg-transparent text-sm"
            >
              <option value="low">低优先级</option>
              <option value="medium">中优先级</option>
              <option value="high">高优先级</option>
              <option value="urgent">紧急</option>
            </select>
            <input
              type="date"
              value={newTask.due_date}
              onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
              className="px-3 py-2 rounded-lg border bg-transparent text-sm"
            />
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowCreate(false)} className="px-3 py-1.5 text-sm rounded-lg hover:bg-[hsl(var(--muted))]">取消</button>
            <button
              onClick={() => createTask.mutate(newTask)}
              disabled={!newTask.title}
              className="px-3 py-1.5 text-sm rounded-lg bg-brand-700 text-white hover:bg-brand-800 disabled:opacity-50"
            >创建</button>
          </div>
        </div>
      )}

      {/* Kanban Board */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kanbanColumns.map((col) => {
          const colTasks = tasks.filter(t => t.status === col.status);
          return (
            <div key={col.status} className="min-h-[200px]">
              <div className="flex items-center gap-2 mb-3">
                <div className={`w-2 h-2 rounded-full ${col.color}`} />
                <span className="text-sm font-semibold">{col.label}</span>
                <span className="text-xs text-[hsl(var(--muted-foreground))] ml-auto bg-[hsl(var(--muted))] rounded-full px-2 py-0.5">
                  {colTasks.length}
                </span>
              </div>
              <div className="space-y-2">
                {colTasks.map((task) => (
                  <div key={task.id} className="p-3 rounded-xl bg-[hsl(var(--card))] border hover:border-brand-300 transition-colors">
                    {task.priority && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        task.priority === "high" || task.priority === "urgent"
                          ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                          : task.priority === "medium"
                          ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                          : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                      }`}>{task.priority}</span>
                    )}
                    <h4 className="text-sm font-medium mt-1.5">{task.title}</h4>
                    {task.description && (
                      <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1 line-clamp-2">{task.description}</p>
                    )}
                    <div className="flex items-center justify-between mt-3">
                      <div className="flex items-center gap-2 text-xs text-[hsl(var(--muted-foreground))]">
                        {task.due_date && <span>{task.due_date}</span>}
                        {task.ai_generated && (
                          <span className="px-1 py-0.5 rounded bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">AI</span>
                        )}
                      </div>
                      <button
                        onClick={() => updateTask.mutate({ id: task.id, status: getNextStatus(task.status) })}
                        className="text-xs text-brand-600 hover:text-brand-700 flex items-center gap-0.5"
                      >
                        推进状态 <ChevronRight className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                ))}
                {colTasks.length === 0 && (
                  <div className="p-4 rounded-xl border border-dashed text-center text-xs text-[hsl(var(--muted-foreground))]">
                    暂无任务
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
