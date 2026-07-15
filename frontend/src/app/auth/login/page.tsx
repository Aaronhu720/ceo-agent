"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/stores/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    organization_name: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isRegister) {
        await register(form);
      } else {
        await login(form.email, form.password);
      }
      router.replace("/chat");
    } catch (err: any) {
      setError(err.message || "操作失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-brand-50 to-blue-100 dark:from-gray-900 dark:to-gray-800">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-brand-700 dark:text-brand-400">CEO Agent</h1>
          <p className="text-[hsl(var(--muted-foreground))] mt-2">企业 AI 合伙人</p>
        </div>

        <div className="bg-[hsl(var(--card))] rounded-2xl shadow-lg p-6">
          <h2 className="text-lg font-semibold mb-4">{isRegister ? "创建账户" : "登录"}</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <>
                <input
                  type="text"
                  placeholder="你的名字"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  required
                />
                <input
                  type="text"
                  placeholder="公司名称"
                  value={form.organization_name}
                  onChange={(e) => setForm({ ...form, organization_name: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  required
                />
              </>
            )}
            <input
              type="email"
              placeholder="邮箱"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full px-4 py-2.5 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            />
            <input
              type="password"
              placeholder="密码"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full px-4 py-2.5 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
              minLength={8}
            />

            {error && <p className="text-sm text-red-500">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-brand-600 text-white font-medium text-sm hover:bg-brand-700 disabled:opacity-50 transition-colors"
            >
              {loading ? "处理中..." : isRegister ? "注册" : "登录"}
            </button>
          </form>

          <div className="mt-4 text-center">
            <button
              onClick={() => { setIsRegister(!isRegister); setError(""); }}
              className="text-sm text-brand-600 hover:underline"
            >
              {isRegister ? "已有账户？登录" : "没有账户？注册"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
