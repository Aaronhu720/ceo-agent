"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/stores/auth";
import { LayoutDashboard, Lock } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login("aaronhu720@gmail.com", password);
      router.replace("/daily");
    } catch (err: any) {
      setError(err.message || "密码错误");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel - branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-brand-900 text-white flex-col justify-between p-12">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-800 flex items-center justify-center">
            <LayoutDashboard className="h-5 w-5 text-brand-300" />
          </div>
          <div>
            <h1 className="text-lg font-bold">CEO Agent</h1>
            <p className="text-[10px] tracking-wider uppercase text-brand-400">Executive Office</p>
          </div>
        </div>

        <div>
          <h2 className="text-3xl font-bold leading-tight mb-4">
            看清经营全局，<br />更从容地做决定
          </h2>
          <p className="text-brand-300 text-sm leading-relaxed max-w-md">
            CEO Agent 是你的企业 AI 合伙人。通过多 Agent 协作，帮你追踪关键指标、
            管理决策流程、积累经营记忆，让每一个决定都有据可依。
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-brand-800/50">
            <p className="text-2xl font-bold text-brand-200">AI</p>
            <p className="text-[10px] text-brand-400 mt-1">经营全景分析</p>
          </div>
          <div className="p-4 rounded-xl bg-brand-800/50">
            <p className="text-2xl font-bold text-brand-200">24/7</p>
            <p className="text-[10px] text-brand-400 mt-1">决策聚焦支持</p>
          </div>
          <div className="p-4 rounded-xl bg-brand-800/50">
            <p className="text-2xl font-bold text-brand-200">Multi</p>
            <p className="text-[10px] text-brand-400 mt-1">专业Agent协同</p>
          </div>
        </div>
      </div>

      {/* Right panel - login form */}
      <div className="flex-1 flex items-center justify-center px-6 bg-[hsl(var(--background))]">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8 lg:hidden">
            <div className="w-14 h-14 rounded-2xl bg-brand-900 flex items-center justify-center mx-auto mb-3">
              <LayoutDashboard className="h-7 w-7 text-brand-300" />
            </div>
            <h1 className="text-2xl font-bold text-brand-800 dark:text-brand-400">CEO Agent</h1>
            <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">企业 AI 合伙人</p>
          </div>

          <div className="lg:text-left text-center mb-6">
            <h2 className="text-xl font-bold">欢迎回来</h2>
            <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">输入密码进入你的 Executive Office</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-[hsl(var(--muted-foreground))]" />
              <input
                type="password"
                placeholder="输入密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                required
                autoFocus
              />
            </div>

            {error && <p className="text-sm text-red-500">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-brand-700 text-white font-medium text-sm hover:bg-brand-800 disabled:opacity-50 transition-colors"
            >
              {loading ? "验证中..." : "进入系统"}
            </button>
          </form>

          <p className="text-center text-[10px] text-[hsl(var(--muted-foreground))] mt-8">
            Powered by CEO Agent · AARON USA LLC
          </p>
        </div>
      </div>
    </div>
  );
}
