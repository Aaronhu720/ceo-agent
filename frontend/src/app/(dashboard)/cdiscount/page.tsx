"use client";
import MarketplacePage from "@/components/marketplace/MarketplacePage";

export default function CdiscountPage() {
  return (
    <MarketplacePage
      config={{
        key: "cdiscount",
        name: "Cdiscount",
        color: "bg-red-100 dark:bg-red-900/30",
        logo: "🇫🇷",
        fields: [
          { key: "app_key", label: "API Login", placeholder: "输入 Cdiscount API Login" },
          { key: "app_secret", label: "API Password", placeholder: "输入 API Password", type: "password" },
          { key: "seller_id", label: "卖家 ID", placeholder: "输入卖家 ID" },
        ],
      }}
    />
  );
}
