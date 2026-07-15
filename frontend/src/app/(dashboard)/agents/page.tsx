"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Bot } from "lucide-react";

interface AgentInfo {
  id: string;
  name: string;
  agent_type: string;
  description: string | null;
  model_provider: string;
  model_name: string;
  status: string;
}

export default function AgentsPage() {
  const { data: agents = [] } = useQuery({
    queryKey: ["agents"],
    queryFn: () => api.get<AgentInfo[]>("/api/agents"),
  });

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      <h1 className="text-xl font-bold">Agent 中心</h1>

      <div className="grid gap-3 sm:grid-cols-2">
        {agents.map((agent) => (
          <div key={agent.id} className="p-4 rounded-xl bg-[hsl(var(--card))] border">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center">
                <Bot className="h-5 w-5 text-brand-600" />
              </div>
              <div>
                <h3 className="font-medium text-sm">{agent.name}</h3>
                <span className="text-xs text-[hsl(var(--muted-foreground))]">{agent.agent_type}</span>
              </div>
            </div>
            {agent.description && (
              <p className="text-sm text-[hsl(var(--muted-foreground))]">{agent.description}</p>
            )}
            <div className="flex items-center gap-2 mt-2 text-xs text-[hsl(var(--muted-foreground))]">
              <span className="px-1.5 py-0.5 rounded bg-[hsl(var(--muted))]">{agent.model_provider}</span>
              <span>{agent.model_name}</span>
            </div>
          </div>
        ))}
        {agents.length === 0 && (
          <div className="col-span-2 text-center text-sm text-[hsl(var(--muted-foreground))] py-8">
            暂无 Agent。系统启动后会自动创建 CEO Agent。
          </div>
        )}
      </div>
    </div>
  );
}
