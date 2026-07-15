"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Bot, Cpu, Code2, BarChart3, Scale, Users, ChevronRight, RefreshCw } from "lucide-react";
import Link from "next/link";

interface AgentInfo {
  id: string;
  name: string;
  agent_type: string;
  description: string | null;
  model_provider: string;
  model_name: string;
  status: string;
}

const agentIcons: Record<string, React.ElementType> = {
  ceo: BarChart3,
  code: Code2,
  finance: Scale,
  market: Cpu,
  hr: Users,
};

const agentDescriptions: Record<string, string> = {
  ceo: "经营分析与决策辅助",
  code: "编程与技术架构",
  finance: "现金流与经营质量",
  market: "竞争与增长机会",
  hr: "组织与关键人才",
};

export default function AgentsPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: agents = [] } = useQuery({
    queryKey: ["agents"],
    queryFn: () => api.get<AgentInfo[]>("/api/agents"),
  });

  const selected = agents.find(a => a.id === selectedId);

  return (
    <div className="max-w-6xl mx-auto px-6 py-6">
      <PageHeader
        tag="Agent Orchestration"
        title="多 Agent 协作面板"
        description="了解各职能 Agent 的工作状态、依赖与最新输出。"
        action={
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))]">
            <RefreshCw className="h-3.5 w-3.5" /> 更新数据
          </button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Grid */}
        <div className="lg:col-span-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {agents.map((agent) => {
              const Icon = agentIcons[agent.agent_type] || Bot;
              const subtitle = agentDescriptions[agent.agent_type] || agent.description;
              return (
                <button
                  key={agent.id}
                  onClick={() => setSelectedId(agent.id)}
                  className="p-5 rounded-xl bg-[hsl(var(--card))] border hover:border-brand-300 transition-colors text-left"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-xl bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center">
                      <Icon className="h-5 w-5 text-brand-700 dark:text-brand-400" />
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className={`w-2 h-2 rounded-full ${
                        agent.status === "active" ? "bg-green-500" : "bg-gray-400"
                      }`} />
                      <span className="text-[10px] text-[hsl(var(--muted-foreground))]">
                        {agent.status === "active" ? "工作中" : "已停用"}
                      </span>
                    </div>
                  </div>
                  <h3 className="font-semibold text-sm">{agent.name}</h3>
                  <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5">{subtitle}</p>
                  <div className="flex items-center justify-between mt-4">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))]">
                        {agent.model_provider}
                      </span>
                      <span className="text-[10px] text-[hsl(var(--muted-foreground))]">{agent.model_name}</span>
                    </div>
                    <span className="text-xs text-brand-600 flex items-center gap-0.5">
                      查看输出 <ChevronRight className="h-3 w-3" />
                    </span>
                  </div>
                </button>
              );
            })}
            {agents.length === 0 && (
              <div className="col-span-2 text-center text-sm text-[hsl(var(--muted-foreground))] py-12">
                暂无 Agent。系统启动后会自动创建 CEO Agent。
              </div>
            )}
          </div>
        </div>

        {/* Right Panel */}
        <div className="space-y-4">
          {/* Collaboration Status */}
          <div className="p-5 rounded-xl bg-brand-900 text-white dark:bg-brand-950">
            <div className="flex items-center gap-2 mb-3">
              <Bot className="h-5 w-5 text-brand-300" />
              <span className="text-sm font-semibold text-brand-200">协作正常</span>
            </div>
            <p className="text-xs text-brand-300">
              当前 {agents.filter(a => a.status === "active").length} 个 Agent 在线工作
            </p>
          </div>

          {/* Selected Agent Detail */}
          {selected && (
            <div className="p-4 rounded-xl bg-[hsl(var(--card))] border space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Selected Agent</p>
              <h3 className="text-lg font-bold">{selected.name}</h3>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">
                {agentDescriptions[selected.agent_type] || selected.description}
              </p>

              <div className="pt-2 space-y-2">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">协作依赖</p>
                <div className="flex gap-2 flex-wrap">
                  <span className="text-xs px-2 py-1 rounded-lg bg-[hsl(var(--muted))]">经营数据</span>
                  <span className="text-xs px-2 py-1 rounded-lg bg-[hsl(var(--muted))]">长期记忆库</span>
                </div>
              </div>

              <Link
                href="/chat"
                className="block w-full text-center py-2.5 rounded-lg bg-brand-700 text-white text-sm hover:bg-brand-800 transition-colors mt-3"
              >
                向该 Agent 追问
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
