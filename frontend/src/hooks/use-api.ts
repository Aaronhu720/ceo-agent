import { useQuery, useMutation, useQueryClient, type UseQueryOptions } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useApiQuery<T>(
  key: string[],
  path: string,
  options?: Omit<UseQueryOptions<T>, "queryKey" | "queryFn">
) {
  return useQuery<T>({
    queryKey: key,
    queryFn: () => api.get<T>(path),
    ...options,
  });
}

export function useApiMutation<TInput = unknown, TOutput = unknown>(
  method: "post" | "patch" | "delete",
  path: string | ((input: TInput) => string),
  options?: {
    invalidateKeys?: string[][];
    onSuccess?: (data: TOutput) => void;
  }
) {
  const queryClient = useQueryClient();

  return useMutation<TOutput, Error, TInput>({
    mutationFn: async (input: TInput) => {
      const url = typeof path === "function" ? path(input) : path;
      switch (method) {
        case "post":
          return api.post<TOutput>(url, input);
        case "patch":
          return api.patch<TOutput>(url, input);
        case "delete":
          return api.delete<TOutput>(url);
      }
    },
    onSuccess: (data) => {
      if (options?.invalidateKeys) {
        for (const key of options.invalidateKeys) {
          queryClient.invalidateQueries({ queryKey: key });
        }
      }
      options?.onSuccess?.(data);
    },
  });
}
