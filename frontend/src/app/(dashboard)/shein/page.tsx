"use client";
import MarketplacePage from "@/components/marketplace/MarketplacePage";

export default function SheinPage() {
  return (
    <MarketplacePage
      config={{
        key: "shein",
        name: "SHEIN",
        color: "bg-black/10 dark:bg-white/10",
        logo: "👗",
        fields: [
          { key: "app_key", label: "Open API Key", placeholder: "输入 SHEIN API Key" },
          { key: "app_secret", label: "API Secret", placeholder: "输入 API Secret", type: "password" },
          { key: "seller_id", label: "卖家 ID", placeholder: "输入 SHEIN 卖家 ID" },
          { key: "shop_name", label: "店铺名称", placeholder: "输入店铺名称" },
        ],
      }}
    />
  );
}
