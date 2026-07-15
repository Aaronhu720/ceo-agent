"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/stores/auth";

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, loadUser } = useAuth();

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    if (!isLoading) {
      router.replace(isAuthenticated ? "/chat" : "/auth/login");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full" />
    </div>
  );
}
