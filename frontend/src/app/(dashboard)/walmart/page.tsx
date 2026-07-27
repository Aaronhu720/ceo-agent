"use client";
import MarketplacePage from "@/components/marketplace/MarketplacePage";

export default function WalmartPage() {
  return (
    <MarketplacePage
      config={{
        key: "walmart",
        name: "Walmart",
        color: "bg-blue-100 dark:bg-blue-900/30",
        logo: "🏪",
        fields: [
          { key: "app_key", label: "Client ID", placeholder: "输入 Walmart Client ID" },
          { key: "app_secret", label: "Client Secret", placeholder: "输入 Client Secret", type: "password" },
          { key: "seller_id", label: "Seller ID", placeholder: "输入卖家 ID" },
        ],
      }}
    />
  );
}
