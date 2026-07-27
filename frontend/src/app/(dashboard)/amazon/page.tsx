"use client";
import MarketplacePage from "@/components/marketplace/MarketplacePage";

export default function AmazonPage() {
  return (
    <MarketplacePage
      config={{
        key: "amazon",
        name: "Amazon",
        color: "bg-orange-100 dark:bg-orange-900/30",
        logo: "📦",
        fields: [
          { key: "seller_id", label: "Seller ID", placeholder: "输入 Amazon Seller ID" },
          { key: "app_key", label: "SP-API Client ID", placeholder: "输入 SP-API Client ID" },
          { key: "app_secret", label: "SP-API Client Secret", placeholder: "输入 Client Secret", type: "password" },
          { key: "shop_name", label: "店铺名称", placeholder: "输入店铺名称" },
        ],
      }}
    />
  );
}
