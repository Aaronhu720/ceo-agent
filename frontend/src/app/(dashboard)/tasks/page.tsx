"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Plus, CheckCircle2, Circle, Clock, AlertTriangle } from "lucide-react";
import type { Task } from "@/types";

const statusFilters = [
  { value: "", label: "全部" },
  { value: "pending", label: "待处理" },
  { value: "in_progress", label: "进行中" },
  { value: "completed", label: "已完成" },
  { value: "at_risk", label: "有风险" },
];

export default function TasksPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newTask, setNewTask] = useState({ title: "", description: "", priority: "medium", due_date: "" });

  const { data: tasks = [] } = useQuery({
    queryKey: ["tasks", statusFilter],
    queryFn: () => api.get<Task[]>(`/api/tasks${statusFilter ? `?status_filter=${statusFilter}` : ""}`),
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

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "in_progress": return <Clock className="h-4 w-4 text-blue-500" />;
      case "at_risk": return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default: return <Circle className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">任务</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm hover:bg-brand-700"
        >
          <Plus className="h-4 w-4" /> 新建
        </button>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1">
        {statusFilters.map((f) => (
          <button
            key={f.value}
            onClick={() => setStatusFilter(f.value)}
            className={cn(
              "px-3 py-1 rounded-full text-xs whitespace-nowrap transition-colors",
              statusFilter === f.value
                ? "bg-brand-600 text-white"
                : "bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))]"
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {showCreate && (
        <div className="p-4 rounded-xl bg-[hsl(var(--card))] border space-y-3">
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
              className="px-3 py-1.5 text-sm rounded-lg bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50"
            >创建</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {tasks.map((task) => (
          <div key={task.id} className="p-3 rounded-xl bg-[hsl(var(--card))] border text-sm">
            <div className="flex items-start gap-3">
              <button
                onClick={() =>
                  updateTask.mutate({
                    id: task.id,
                    status: task.status === "completed" ? "pending" : "completed",
                  })
                }
                className="mt-0.5 shrink-0"
              >
                {statusIcon(task.status)}
              </button>
              <div className="flex-1 min-w-0">
                <p className={cn("font-medium", task.status === "completed" && "line-through text-[hsl(var(--muted-foreground))]")}>
                  {task.title}
                </p>
                {task.description && (
                  <p className="text-[hsl(var(--muted-foreground))] mt-0.5 text-xs">{task.description}</p>
                )}
                <div className="flex items-center gap-2 mt-1.5">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    task.priority === "high" || task.priority === "urgent" ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" :
                    task.priority === "medium" ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" :
                    "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                  }`}>{task.priority}</span>
                  {task.due_date && <span className="text-xs text-[hsl(var(--muted-foreground))]">截止: {task.due_date}</span>}
                  {task.ai_generated && <span className="text-xs px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">AI</span>}
                </div>
              </div>
            </div>
          </div>
        ))}
        {tasks.length === 0 && (
          <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-8">暂无任务</p>
        )}
      </div>
    </div>
  );
}
