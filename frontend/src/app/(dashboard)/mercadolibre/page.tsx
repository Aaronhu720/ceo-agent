"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  Globe, Plus, Link2, Unlink, ExternalLink, Loader2, Check, AlertCircle,
  Store, Package, Trash2, Settings, ChevronDown, ChevronUp,
} from "lucide-react";

interface MLSite {
  site_id: string;
  country: string;
  domain: string;
  currency: string;
}

interface MLAccount {
  id: string;
  site_id: string;
  country_name: string;
  seller_id: string | null;
  nickname: string | null;
  status: string;
  app_id: string | null;
  has_secret: boolean;
  redirect_uri: string | null;
  total_listings: number;
  active_listings: number;
  token_expires_at: string | null;
  created_at: string;
}

interface MLStats {
  total_accounts: number;
  connected_accounts: number;
  total_listings: number;
}

const FLAG_EMOJI: Record<string, string> = {
  MLM: "🇲🇽", MLB: "🇧🇷", MLC: "🇨🇱", MLA: "🇦🇷",
  MCO: "🇨🇴", MLU: "🇺🇾", MPE: "🇵🇪", MEC: "🇪🇨",
  MCR: "🇨🇷", MPA: "🇵🇦", MLV: "🇻🇪", MRD: "🇩🇴",
  MBO: "🇧🇴", MPY: "🇵🇾", MGT: "🇬🇹", MHN: "🇭🇳",
  MNI: "🇳🇮", MSV: "🇸🇻",
};

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending: { label: "待配置", color: "text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20" },
  connected: { label: "已连接", color: "text-green-600 bg-green-50 dark:bg-green-900/20" },
  disconnected: { label: "已断开", color: "text-red-600 bg-red-50 dark:bg-red-900/20" },
  error: { label: "错误", color: "text-red-600 bg-red-50 dark:bg-red-900/20" },
};

export default function MercadoLibrePage() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [expandedAccount, setExpandedAccount] = useState<string | null>(null);
  const [configForm, setConfigForm] = useState<Record<string, string>>({});

  const { data: sites = [] } = useQuery({
    queryKey: ["ml-sites"],
    queryFn: () => api.get<MLSite[]>("/api/mercadolibre/sites"),
  });

  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ["ml-accounts"],
    queryFn: () => api.get<MLAccount[]>("/api/mercadolibre/accounts"),
  });

  const { data: stats } = useQuery({
    queryKey: ["ml-stats"],
    queryFn: () => api.get<MLStats>("/api/mercadolibre/stats"),
  });

  const addAccount = useMutation({
    mutationFn: (siteId: string) =>
      api.post("/api/mercadolibre/accounts", { site_id: siteId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ml-accounts"] });
      queryClient.invalidateQueries({ queryKey: ["ml-stats"] });
      setShowAddModal(false);
    },
  });

  const updateAccount = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      api.put(`/api/mercadolibre/accounts/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ml-accounts"] });
    },
  });

  const deleteAccount = useMutation({
    mutationFn: (id: string) => api.delete(`/api/mercadolibre/accounts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ml-accounts"] });
      queryClient.invalidateQueries({ queryKey: ["ml-stats"] });
    },
  });

  const getAuthUrl = useMutation({
    mutationFn: (id: string) =>
      api.get<{ auth_url: string }>(`/api/mercadolibre/accounts/${id}/auth-url`),
    onSuccess: (data) => {
      window.open(data.auth_url, "_blank");
    },
  });

  const connectedSiteIds = new Set(accounts.map((a) => a.site_id));
  const availableSites = sites.filter((s) => !connectedSiteIds.has(s.site_id));

  const handleSaveConfig = (accountId: string) => {
    const data: any = {};
    if (configForm[`${accountId}_app_id`]) data.app_id = configForm[`${accountId}_app_id`];
    if (configForm[`${accountId}_app_secret`]) data.app_secret = configForm[`${accountId}_app_secret`];
    updateAccount.mutate({ id: accountId, data });
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
              <Store className="h-5 w-5 text-yellow-600" />
            </div>
            Mercado Libre 多国管理
          </h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">
            管理你在各个拉美国家的美客多店铺和产品上架
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-700 text-white hover:bg-brand-800 transition-colors text-sm font-medium"
        >
          <Plus className="h-4 w-4" />
          添加国家站点
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-[hsl(var(--card))] border">
          <p className="text-sm text-[hsl(var(--muted-foreground))]">已添加站点</p>
          <p className="text-2xl font-bold mt-1">{stats?.total_accounts || 0}</p>
        </div>
        <div className="p-4 rounded-xl bg-[hsl(var(--card))] border">
          <p className="text-sm text-[hsl(var(--muted-foreground))]">已连接</p>
          <p className="text-2xl font-bold mt-1 text-green-600">{stats?.connected_accounts || 0}</p>
        </div>
        <div className="p-4 rounded-xl bg-[hsl(var(--card))] border">
          <p className="text-sm text-[hsl(var(--muted-foreground))]">商品总数</p>
          <p className="text-2xl font-bold mt-1">{stats?.total_listings || 0}</p>
        </div>
      </div>

      {/* Account List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-brand-600" />
        </div>
      ) : accounts.length === 0 ? (
        <div className="text-center py-20 bg-[hsl(var(--card))] rounded-xl border">
          <Globe className="h-12 w-12 mx-auto text-[hsl(var(--muted-foreground))] mb-3" />
          <p className="text-lg font-medium">还没有添加任何站点</p>
          <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">
            点击"添加国家站点"开始连接你的美客多店铺
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {accounts.map((account) => {
            const status = STATUS_MAP[account.status] || STATUS_MAP.pending;
            const isExpanded = expandedAccount === account.id;

            return (
              <div key={account.id} className="bg-[hsl(var(--card))] border rounded-xl overflow-hidden">
                <div
                  className="flex items-center gap-4 p-4 cursor-pointer hover:bg-[hsl(var(--muted))]/30 transition-colors"
                  onClick={() => setExpandedAccount(isExpanded ? null : account.id)}
                >
                  <span className="text-2xl">{FLAG_EMOJI[account.site_id] || "🌎"}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{account.country_name}</span>
                      <span className="text-xs text-[hsl(var(--muted-foreground))]">{account.site_id}</span>
                    </div>
                    {account.nickname && (
                      <p className="text-sm text-[hsl(var(--muted-foreground))]">
                        卖家: {account.nickname} ({account.seller_id})
                      </p>
                    )}
                  </div>
                  <span className={cn("text-xs px-2.5 py-1 rounded-full font-medium", status.color)}>
                    {status.label}
                  </span>
                  <div className="text-sm text-[hsl(var(--muted-foreground))]">
                    {account.active_listings} 个在售
                  </div>
                  {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </div>

                {isExpanded && (
                  <div className="border-t px-4 py-4 space-y-4">
                    {/* API Configuration */}
                    <div className="space-y-3">
                      <h3 className="text-sm font-semibold flex items-center gap-2">
                        <Settings className="h-4 w-4" /> API 配置
                      </h3>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-xs text-[hsl(var(--muted-foreground))]">App ID (Client ID)</label>
                          <input
                            type="text"
                            defaultValue={account.app_id || ""}
                            onChange={(e) =>
                              setConfigForm((f) => ({ ...f, [`${account.id}_app_id`]: e.target.value }))
                            }
                            placeholder="输入 Mercado Libre App ID"
                            className="w-full mt-1 px-3 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-[hsl(var(--muted-foreground))]">
                            App Secret {account.has_secret && <Check className="inline h-3 w-3 text-green-500" />}
                          </label>
                          <input
                            type="password"
                            placeholder={account.has_secret ? "已配置（重新输入覆盖）" : "输入 App Secret"}
                            onChange={(e) =>
                              setConfigForm((f) => ({ ...f, [`${account.id}_app_secret`]: e.target.value }))
                            }
                            className="w-full mt-1 px-3 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                          />
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleSaveConfig(account.id)}
                          disabled={updateAccount.isPending}
                          className="px-4 py-2 rounded-lg bg-brand-700 text-white text-sm hover:bg-brand-800 disabled:opacity-50"
                        >
                          {updateAccount.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "保存配置"}
                        </button>
                        {account.app_id && (
                          <button
                            onClick={() => getAuthUrl.mutate(account.id)}
                            disabled={getAuthUrl.isPending}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-600 text-white text-sm hover:bg-green-700 disabled:opacity-50"
                          >
                            <Link2 className="h-4 w-4" />
                            {account.status === "connected" ? "重新授权" : "授权连接"}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Account Info */}
                    {account.status === "connected" && (
                      <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20 text-sm">
                        <div className="flex items-center gap-2 text-green-700 dark:text-green-400 font-medium">
                          <Check className="h-4 w-4" />
                          已连接到 Mercado Libre {account.country_name}
                        </div>
                        {account.token_expires_at && (
                          <p className="text-xs text-green-600 dark:text-green-500 mt-1">
                            Token 过期时间: {new Date(account.token_expires_at).toLocaleString("zh-CN")}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex justify-end gap-2 pt-2 border-t">
                      <button
                        onClick={() => {
                          if (confirm(`确定删除 ${account.country_name} 站点吗？`)) {
                            deleteAccount.mutate(account.id);
                          }
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 text-sm"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        删除站点
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add Site Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[hsl(var(--card))] rounded-2xl w-full max-w-lg max-h-[80vh] overflow-hidden">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="font-semibold">选择要添加的国家站点</h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
              >
                ✕
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[60vh] space-y-2">
              {availableSites.length === 0 ? (
                <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-8">
                  所有站点都已添加
                </p>
              ) : (
                availableSites.map((site) => (
                  <button
                    key={site.site_id}
                    onClick={() => addAccount.mutate(site.site_id)}
                    disabled={addAccount.isPending}
                    className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-[hsl(var(--muted))] transition-colors text-left"
                  >
                    <span className="text-2xl">{FLAG_EMOJI[site.site_id] || "🌎"}</span>
                    <div className="flex-1">
                      <p className="font-medium">{site.country}</p>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">
                        {site.domain} · {site.currency}
                      </p>
                    </div>
                    <span className="text-xs text-[hsl(var(--muted-foreground))]">{site.site_id}</span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
