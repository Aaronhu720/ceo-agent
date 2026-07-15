"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/stores/auth";

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
      router.replace("/chat");
    } catch (err: any) {
      setError(err.message || "密码错误");
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
          <h2 className="text-lg font-semibold mb-4">输入密码进入</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="password"
              placeholder="密码"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
              autoFocus
            />

            {error && <p className="text-sm text-red-500">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-brand-600 text-white font-medium text-sm hover:bg-brand-700 disabled:opacity-50 transition-colors"
            >
              {loading ? "验证中..." : "进入"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
