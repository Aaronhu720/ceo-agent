"use client";
import MarketplacePage from "@/components/marketplace/MarketplacePage";

export default function WayfairPage() {
  return (
    <MarketplacePage
      config={{
        key: "wayfair",
        name: "Wayfair",
        color: "bg-purple-100 dark:bg-purple-900/30",
        logo: "🏠",
        fields: [
          { key: "app_key", label: "Client ID", placeholder: "输入 Wayfair Client ID" },
          { key: "app_secret", label: "Client Secret", placeholder: "输入 Client Secret", type: "password" },
          { key: "seller_id", label: "Supplier ID", placeholder: "输入 Supplier ID" },
          { key: "shop_name", label: "店铺名称", placeholder: "输入店铺名称" },
        ],
      }}
    />
  );
}
