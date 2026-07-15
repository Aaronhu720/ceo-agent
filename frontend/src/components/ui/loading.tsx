"use client";

import { cn } from "@/lib/utils";

export function Spinner({ className }: { className?: string }) {
  return (
    <div className={cn("animate-spin h-5 w-5 border-2 border-brand-500 border-t-transparent rounded-full", className)} />
  );
}

export function PageLoading() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <Spinner className="h-8 w-8" />
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && <div className="mb-3 text-[hsl(var(--muted-foreground))]">{icon}</div>}
      <h3 className="text-sm font-medium">{title}</h3>
      {description && (
        <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1 max-w-sm">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
