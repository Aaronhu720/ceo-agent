"use client";
import MarketplacePage from "@/components/marketplace/MarketplacePage";

export default function OttoPage() {
  return (
    <MarketplacePage
      config={{
        key: "otto",
        name: "OTTO",
        color: "bg-red-100 dark:bg-red-900/30",
        logo: "🇩🇪",
        fields: [
          { key: "app_key", label: "API Username", placeholder: "输入 OTTO API Username" },
          { key: "app_secret", label: "API Password", placeholder: "输入 API Password", type: "password" },
          { key: "seller_id", label: "Partner ID", placeholder: "输入 Partner ID" },
          { key: "shop_name", label: "店铺名称", placeholder: "输入店铺名称" },
        ],
      }}
    />
  );
}
