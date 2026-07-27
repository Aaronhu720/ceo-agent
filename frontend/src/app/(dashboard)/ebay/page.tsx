"use client";
import MarketplacePage from "@/components/marketplace/MarketplacePage";

export default function EbayPage() {
  return (
    <MarketplacePage
      config={{
        key: "ebay",
        name: "eBay",
        color: "bg-red-100 dark:bg-red-900/30",
        logo: "🛒",
        fields: [
          { key: "app_key", label: "App ID (Client ID)", placeholder: "输入 eBay App ID" },
          { key: "app_secret", label: "Cert ID (Client Secret)", placeholder: "输入 Cert ID", type: "password" },
          { key: "seller_id", label: "卖家账号", placeholder: "输入 eBay 卖家账号" },
        ],
      }}
    />
  );
}
