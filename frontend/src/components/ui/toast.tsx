"use client";

import { useState, useEffect, createContext, useContext, useCallback } from "react";
import { cn } from "@/lib/utils";
import { X, CheckCircle2, AlertTriangle, Info } from "lucide-react";

interface Toast {
  id: string;
  type: "success" | "error" | "info" | "warning";
  title: string;
  description?: string;
}

interface ToastContextType {
  toast: (t: Omit<Toast, "id">) => void;
}

const ToastContext = createContext<ToastContextType>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((t: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { ...t, id }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 4000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const icons = {
    success: <CheckCircle2 className="h-4 w-4 text-green-500" />,
    error: <AlertTriangle className="h-4 w-4 text-red-500" />,
    warning: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
    info: <Info className="h-4 w-4 text-blue-500" />,
  };

  return (
    <ToastContext.Provider value={{ toast: addToast }}>
      {children}
      <div className="fixed bottom-20 lg:bottom-4 right-4 z-50 space-y-2 max-w-sm">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "flex items-start gap-2 p-3 rounded-xl shadow-lg border text-sm animate-in slide-in-from-right",
              "bg-[hsl(var(--card))]"
            )}
          >
            {icons[t.type]}
            <div className="flex-1">
              <p className="font-medium">{t.title}</p>
              {t.description && (
                <p className="text-[hsl(var(--muted-foreground))] text-xs mt-0.5">{t.description}</p>
              )}
            </div>
            <button onClick={() => removeToast(t.id)} className="shrink-0">
              <X className="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
