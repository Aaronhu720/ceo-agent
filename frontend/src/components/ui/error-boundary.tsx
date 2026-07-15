"use client";

import { Component, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex flex-col items-center justify-center min-h-[30vh] p-6">
          <AlertTriangle className="h-10 w-10 text-red-500 mb-3" />
          <h2 className="text-base font-semibold mb-1">出错了</h2>
          <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4 text-center max-w-md">
            {this.state.error?.message || "发生了未知错误"}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-4 py-2 bg-brand-500 text-white rounded-lg text-sm hover:bg-brand-600 transition-colors"
          >
            重试
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
