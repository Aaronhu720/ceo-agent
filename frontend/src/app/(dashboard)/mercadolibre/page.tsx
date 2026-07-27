"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  Globe, Plus, Link2, ExternalLink, Loader2, Check, AlertCircle,
  Store, Package, Trash2, Settings, ChevronDown, ChevronUp,
  Eye, Upload, Image, DollarSign, Tag, ShoppingCart,
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

interface MLListingRecord {
  id: string;
  ml_item_id: string;
  pim_sku: string | null;
  title: string;
  price: number | null;
  currency_id: string | null;
  permalink: string | null;
  ml_status: string | null;
  created_at: string;
}

interface PreviewData {
  listing_data: {
    title: string;
    category_id: string | null;
    price: number;
    currency_id: string;
    available_quantity: number;
    attributes: { id: string; value_name: string }[];
    _description: string;
    pim_images: string[];
    seller_custom_field: string;
  };
  pim_product: Record<string, unknown>;
  category_attributes: { id: string; name: string; required: boolean }[];
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

  // Publishing state
  const [activeTab, setActiveTab] = useState<"accounts" | "publish" | "listings">("accounts");
  const [selectedAccountId, setSelectedAccountId] = useState<string>("");
  const [searchSku, setSearchSku] = useState("");
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [publishPrice, setPublishPrice] = useState<string>("");
  const [titleOverride, setTitleOverride] = useState("");
  const [publishResult, setPublishResult] = useState<{
    success: boolean;
    item_id?: string;
    permalink?: string;
    error?: unknown;
  } | null>(null);

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

  const connectedAccounts = accounts.filter((a) => a.status === "connected");

  const { data: listings = [], isLoading: listingsLoading } = useQuery({
    queryKey: ["ml-listings", selectedAccountId],
    queryFn: () => {
      const params = selectedAccountId ? `?account_id=${selectedAccountId}` : "";
      return api.get<MLListingRecord[]>(`/api/mercadolibre/listings${params}`);
    },
    enabled: activeTab === "listings",
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
    mutationFn: ({ id, data }: { id: string; data: unknown }) =>
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

  const previewMutation = useMutation({
    mutationFn: (body: { account_id: string; pim_sku: string; price?: number; title_override?: string }) =>
      api.post<PreviewData>("/api/mercadolibre/preview-listing", body),
    onSuccess: (data) => {
      setPreviewData(data);
      if (data.listing_data.price) {
        setPublishPrice(String(data.listing_data.price));
      }
      setTitleOverride(data.listing_data.title);
    },
  });

  const publishMutation = useMutation({
    mutationFn: (body: { account_id: string; pim_sku: string; price?: number; title_override?: string }) =>
      api.post<{ success: boolean; item_id?: string; permalink?: string; error?: unknown }>(
        "/api/mercadolibre/publish-from-pim",
        body
      ),
    onSuccess: (data) => {
      setPublishResult(data);
      if (data.success) {
        queryClient.invalidateQueries({ queryKey: ["ml-listings"] });
        queryClient.invalidateQueries({ queryKey: ["ml-stats"] });
      }
    },
  });

  const connectedSiteIds = new Set(accounts.map((a) => a.site_id));
  const availableSites = sites.filter((s) => !connectedSiteIds.has(s.site_id));

  const handleSaveConfig = (accountId: string) => {
    const data: Record<string, string> = {};
    if (configForm[`${accountId}_app_id`]) data.app_id = configForm[`${accountId}_app_id`];
    if (configForm[`${accountId}_app_secret`]) data.app_secret = configForm[`${accountId}_app_secret`];
    updateAccount.mutate({ id: accountId, data });
  };

  const handlePreview = () => {
    if (!selectedAccountId || !searchSku.trim()) return;
    setPreviewData(null);
    setPublishResult(null);
    previewMutation.mutate({
      account_id: selectedAccountId,
      pim_sku: searchSku.trim(),
      price: publishPrice ? parseFloat(publishPrice) : undefined,
    });
  };

  const handlePublish = () => {
    if (!selectedAccountId || !searchSku.trim()) return;
    publishMutation.mutate({
      account_id: selectedAccountId,
      pim_sku: searchSku.trim(),
      price: publishPrice ? parseFloat(publishPrice) : undefined,
      title_override: titleOverride || undefined,
    });
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

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-[hsl(var(--muted))] rounded-xl w-fit">
        {([
          { key: "accounts" as const, label: "店铺账号", icon: Store },
          { key: "publish" as const, label: "产品上架", icon: Upload },
          { key: "listings" as const, label: "已上架商品", icon: Package },
        ]).map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
              activeTab === key
                ? "bg-[hsl(var(--card))] text-[hsl(var(--foreground))] shadow-sm"
                : "text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content: Accounts */}
      {activeTab === "accounts" && (
        <>
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
        </>
      )}

      {/* Tab Content: Publish */}
      {activeTab === "publish" && (
        <div className="space-y-4">
          {connectedAccounts.length === 0 ? (
            <div className="text-center py-16 bg-[hsl(var(--card))] rounded-xl border">
              <AlertCircle className="h-10 w-10 mx-auto text-yellow-500 mb-3" />
              <p className="font-medium">没有已连接的店铺</p>
              <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">
                请先在"店铺账号"标签页中连接一个美客多店铺
              </p>
            </div>
          ) : (
            <>
              {/* Search & Config Bar */}
              <div className="bg-[hsl(var(--card))] border rounded-xl p-4 space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <ShoppingCart className="h-4 w-4" />
                  从产品数据库上架到美客多
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {/* Account selector */}
                  <div>
                    <label className="text-xs text-[hsl(var(--muted-foreground))] mb-1 block">选择店铺</label>
                    <select
                      value={selectedAccountId}
                      onChange={(e) => setSelectedAccountId(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="">选择一个已连接的店铺</option>
                      {connectedAccounts.map((a) => (
                        <option key={a.id} value={a.id}>
                          {FLAG_EMOJI[a.site_id] || "🌎"} {a.country_name} - {a.nickname || a.site_id}
                        </option>
                      ))}
                    </select>
                  </div>
                  {/* SKU input */}
                  <div>
                    <label className="text-xs text-[hsl(var(--muted-foreground))] mb-1 block">产品 SKU</label>
                    <input
                      type="text"
                      value={searchSku}
                      onChange={(e) => setSearchSku(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handlePreview()}
                      placeholder="输入产品SKU，如 DC-1001"
                      className="w-full px-3 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                  {/* Price override */}
                  <div>
                    <label className="text-xs text-[hsl(var(--muted-foreground))] mb-1 block">
                      <DollarSign className="inline h-3 w-3" /> 价格 (MXN)
                    </label>
                    <input
                      type="number"
                      value={publishPrice}
                      onChange={(e) => setPublishPrice(e.target.value)}
                      placeholder="留空自动计算"
                      className="w-full px-3 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handlePreview}
                    disabled={!selectedAccountId || !searchSku.trim() || previewMutation.isPending}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {previewMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                    预览 Listing
                  </button>
                </div>
              </div>

              {/* Preview Error */}
              {previewMutation.isError && (
                <div className="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                  <div className="flex items-center gap-2 text-red-700 dark:text-red-400 font-medium text-sm">
                    <AlertCircle className="h-4 w-4" />
                    预览失败: {(previewMutation.error as Error)?.message || "未知错误"}
                  </div>
                </div>
              )}

              {/* Preview Result */}
              {previewData && (
                <div className="bg-[hsl(var(--card))] border rounded-xl overflow-hidden">
                  <div className="p-4 border-b bg-blue-50 dark:bg-blue-900/20">
                    <h3 className="font-semibold flex items-center gap-2 text-blue-800 dark:text-blue-300">
                      <Eye className="h-4 w-4" />
                      Listing 预览
                    </h3>
                  </div>
                  <div className="p-4 space-y-4">
                    {/* Title edit */}
                    <div>
                      <label className="text-xs text-[hsl(var(--muted-foreground))] mb-1 flex items-center gap-1">
                        <Tag className="h-3 w-3" />
                        标题 (西班牙语, 最多60字符)
                        <span className={cn(
                          "ml-2 font-mono",
                          titleOverride.length > 60 ? "text-red-500" : "text-[hsl(var(--muted-foreground))]"
                        )}>
                          {titleOverride.length}/60
                        </span>
                      </label>
                      <input
                        type="text"
                        value={titleOverride}
                        onChange={(e) => setTitleOverride(e.target.value)}
                        maxLength={60}
                        className="w-full px-3 py-2 rounded-lg border bg-transparent text-sm font-medium focus:outline-none focus:ring-2 focus:ring-brand-500"
                      />
                    </div>

                    {/* Info grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="p-3 rounded-lg bg-[hsl(var(--muted))]">
                        <p className="text-xs text-[hsl(var(--muted-foreground))]">分类</p>
                        <p className="text-sm font-medium mt-0.5 truncate">{previewData.listing_data.category_id || "未找到"}</p>
                      </div>
                      <div className="p-3 rounded-lg bg-[hsl(var(--muted))]">
                        <p className="text-xs text-[hsl(var(--muted-foreground))]">价格</p>
                        <p className="text-sm font-medium mt-0.5">
                          ${previewData.listing_data.price} {previewData.listing_data.currency_id}
                        </p>
                      </div>
                      <div className="p-3 rounded-lg bg-[hsl(var(--muted))]">
                        <p className="text-xs text-[hsl(var(--muted-foreground))]">库存</p>
                        <p className="text-sm font-medium mt-0.5">{previewData.listing_data.available_quantity}</p>
                      </div>
                      <div className="p-3 rounded-lg bg-[hsl(var(--muted))]">
                        <p className="text-xs text-[hsl(var(--muted-foreground))]">SKU</p>
                        <p className="text-sm font-medium mt-0.5">{previewData.listing_data.seller_custom_field}</p>
                      </div>
                    </div>

                    {/* Attributes */}
                    {previewData.listing_data.attributes.length > 0 && (
                      <div>
                        <p className="text-xs text-[hsl(var(--muted-foreground))] mb-2">属性</p>
                        <div className="flex flex-wrap gap-2">
                          {previewData.listing_data.attributes.map((attr) => (
                            <span key={attr.id} className="px-2 py-1 rounded-md bg-[hsl(var(--muted))] text-xs">
                              {attr.id}: {attr.value_name}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Description */}
                    <div>
                      <p className="text-xs text-[hsl(var(--muted-foreground))] mb-2">描述 (西班牙语)</p>
                      <div className="p-3 rounded-lg bg-[hsl(var(--muted))] text-sm whitespace-pre-wrap max-h-40 overflow-y-auto">
                        {previewData.listing_data._description}
                      </div>
                    </div>

                    {/* Images */}
                    {previewData.listing_data.pim_images && previewData.listing_data.pim_images.length > 0 && (
                      <div>
                        <p className="text-xs text-[hsl(var(--muted-foreground))] mb-2 flex items-center gap-1">
                          <Image className="h-3 w-3" />
                          产品原图 ({previewData.listing_data.pim_images.length} 张)
                        </p>
                        <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
                          {previewData.listing_data.pim_images.map((url, i) => (
                            <div key={i} className="aspect-square rounded-lg border overflow-hidden bg-white">
                              <img
                                src={url}
                                alt={`Product image ${i + 1}`}
                                className="w-full h-full object-contain"
                                loading="lazy"
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* PIM Product raw info */}
                    <details className="text-xs">
                      <summary className="cursor-pointer text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]">
                        查看 PIM 原始数据
                      </summary>
                      <pre className="mt-2 p-3 rounded-lg bg-[hsl(var(--muted))] overflow-x-auto max-h-48 overflow-y-auto">
                        {JSON.stringify(previewData.pim_product, null, 2)}
                      </pre>
                    </details>

                    {/* Publish button */}
                    <div className="flex items-center gap-3 pt-3 border-t">
                      <button
                        onClick={handlePublish}
                        disabled={publishMutation.isPending}
                        className="flex items-center gap-2 px-6 py-3 rounded-xl bg-yellow-500 text-black text-sm font-bold hover:bg-yellow-400 disabled:opacity-50 transition-colors"
                      >
                        {publishMutation.isPending ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            正在上架到美客多...
                          </>
                        ) : (
                          <>
                            <Upload className="h-4 w-4" />
                            确认上架到 Mercado Libre
                          </>
                        )}
                      </button>
                      {publishPrice && (
                        <span className="text-sm text-[hsl(var(--muted-foreground))]">
                          售价: ${publishPrice} MXN
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Publish Result */}
              {publishResult && (
                <div className={cn(
                  "p-4 rounded-xl border",
                  publishResult.success
                    ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
                    : "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
                )}>
                  {publishResult.success ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-green-700 dark:text-green-400 font-medium">
                        <Check className="h-5 w-5" />
                        上架成功!
                      </div>
                      <p className="text-sm text-green-600 dark:text-green-500">
                        Item ID: {publishResult.item_id}
                      </p>
                      {publishResult.permalink && (
                        <a
                          href={publishResult.permalink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 underline"
                        >
                          <ExternalLink className="h-3.5 w-3.5" />
                          在美客多上查看
                        </a>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-red-700 dark:text-red-400 font-medium">
                        <AlertCircle className="h-5 w-5" />
                        上架失败
                      </div>
                      <pre className="text-xs text-red-600 dark:text-red-400 whitespace-pre-wrap">
                        {JSON.stringify(publishResult.error, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Tab Content: Listings */}
      {activeTab === "listings" && (
        <div className="space-y-4">
          {/* Filter */}
          <div className="flex items-center gap-3">
            <select
              value={selectedAccountId}
              onChange={(e) => setSelectedAccountId(e.target.value)}
              className="px-3 py-2 rounded-lg border bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">全部店铺</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {FLAG_EMOJI[a.site_id] || "🌎"} {a.country_name}
                </option>
              ))}
            </select>
            <span className="text-sm text-[hsl(var(--muted-foreground))]">
              共 {listings.length} 个商品
            </span>
          </div>

          {listingsLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
            </div>
          ) : listings.length === 0 ? (
            <div className="text-center py-16 bg-[hsl(var(--card))] rounded-xl border">
              <Package className="h-10 w-10 mx-auto text-[hsl(var(--muted-foreground))] mb-3" />
              <p className="font-medium">还没有上架任何商品</p>
              <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">
                在"产品上架"标签页中上架你的第一个产品
              </p>
            </div>
          ) : (
            <div className="bg-[hsl(var(--card))] border rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-[hsl(var(--muted))]/50">
                      <th className="text-left px-4 py-3 font-medium text-[hsl(var(--muted-foreground))]">ML Item ID</th>
                      <th className="text-left px-4 py-3 font-medium text-[hsl(var(--muted-foreground))]">标题</th>
                      <th className="text-left px-4 py-3 font-medium text-[hsl(var(--muted-foreground))]">SKU</th>
                      <th className="text-right px-4 py-3 font-medium text-[hsl(var(--muted-foreground))]">价格</th>
                      <th className="text-center px-4 py-3 font-medium text-[hsl(var(--muted-foreground))]">状态</th>
                      <th className="text-right px-4 py-3 font-medium text-[hsl(var(--muted-foreground))]">上架时间</th>
                      <th className="px-4 py-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {listings.map((listing) => (
                      <tr key={listing.id} className="border-b last:border-0 hover:bg-[hsl(var(--muted))]/30">
                        <td className="px-4 py-3 font-mono text-xs">{listing.ml_item_id}</td>
                        <td className="px-4 py-3 max-w-[200px] truncate">{listing.title}</td>
                        <td className="px-4 py-3 text-xs">{listing.pim_sku || "-"}</td>
                        <td className="px-4 py-3 text-right">
                          {listing.price != null ? `$${listing.price} ${listing.currency_id || ""}` : "-"}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={cn(
                            "text-xs px-2 py-0.5 rounded-full",
                            listing.ml_status === "active"
                              ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                              : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                          )}>
                            {listing.ml_status || "unknown"}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right text-xs text-[hsl(var(--muted-foreground))]">
                          {new Date(listing.created_at).toLocaleString("zh-CN")}
                        </td>
                        <td className="px-4 py-3">
                          {listing.permalink && (
                            <a
                              href={listing.permalink}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-700"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
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
