"use client";
import MarketplacePage from "@/components/marketplace/MarketplacePage";

export default function TemuPage() {
  return (
    <MarketplacePage
      config={{
        key: "temu",
        name: "Temu",
        color: "bg-orange-100 dark:bg-orange-900/30",
        logo: "🟠",
        fields: [
          { key: "app_key", label: "App Key", placeholder: "输入 Temu App Key" },
          { key: "app_secret", label: "App Secret", placeholder: "输入 App Secret", type: "password" },
          { key: "seller_id", label: "卖家 ID", placeholder: "输入卖家 ID" },
          { key: "shop_name", label: "店铺名称", placeholder: "输入店铺名称" },
        ],
      }}
    />
  );
}
