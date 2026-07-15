"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Home, MessageSquare, CheckSquare, FolderKanban, User } from "lucide-react";

const mobileNavItems = [
  { href: "/daily", label: "首页", icon: Home },
  { href: "/chat", label: "Agent", icon: MessageSquare },
  { href: "/tasks", label: "任务", icon: CheckSquare },
  { href: "/projects", label: "项目", icon: FolderKanban },
  { href: "/settings", label: "我的", icon: User },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-[hsl(var(--card))] border-t safe-area-bottom">
      <div className="flex items-center justify-around h-14">
        {mobileNavItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center gap-0.5 px-3 py-1 text-xs transition-colors",
              pathname === item.href
                ? "text-brand-600"
                : "text-[hsl(var(--muted-foreground))]"
            )}
          >
            <item.icon className="h-5 w-5" />
            <span>{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
