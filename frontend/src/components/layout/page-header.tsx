"use client";

interface PageHeaderProps {
  tag: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function PageHeader({ tag, title, description, action }: PageHeaderProps) {
  return (
    <div className="mb-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold tracking-wider uppercase text-brand-600 mb-1">{tag}</p>
          <h1 className="text-2xl font-bold text-[hsl(var(--foreground))]">{title}</h1>
          {description && (
            <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">{description}</p>
          )}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
    </div>
  );
}
