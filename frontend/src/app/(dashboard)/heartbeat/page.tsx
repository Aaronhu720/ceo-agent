"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { HeartPulse, Play } from "lucide-react";

interface HeartbeatRule {
  id: string;
  name: string;
  description: string | null;
  frequency_type: string;
  cron_expression: string | null;
  check_type: string;
  priority: string;
  enabled: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
}

export default function HeartbeatPage() {
  const { data: rules = [] } = useQuery({
    queryKey: ["heartbeat-rules"],
    queryFn: () => api.get<HeartbeatRule[]>("/api/heartbeat-rules"),
  });

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      <h1 className="text-xl font-bold">Heartbeat</h1>
      <p className="text-sm text-[hsl(var(--muted-foreground))]">自动巡检和定时任务</p>

      <div className="space-y-3">
        {rules.map((rule) => (
          <div key={rule.id} className="p-4 rounded-xl bg-[hsl(var(--card))] border">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <HeartPulse className={`h-5 w-5 mt-0.5 ${rule.enabled ? "text-green-500" : "text-gray-400"}`} />
                <div>
                  <h3 className="text-sm font-medium">{rule.name}</h3>
                  {rule.description && (
                    <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5">{rule.description}</p>
                  )}
                  <div className="flex items-center gap-2 mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                    <span className="px-1.5 py-0.5 rounded bg-[hsl(var(--muted))]">{rule.frequency_type}</span>
                    {rule.cron_expression && <span>{rule.cron_expression}</span>}
                    <span className={rule.enabled ? "text-green-600" : "text-gray-400"}>
                      {rule.enabled ? "启用" : "停用"}
                    </span>
                  </div>
                </div>
              </div>
              <button className="p-1.5 rounded-lg hover:bg-[hsl(var(--muted))] transition-colors">
                <Play className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
        {rules.length === 0 && (
          <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-8">
            Heartbeat 规则将在系统启动后自动创建
          </p>
        )}
      </div>
    </div>
  );
}
