import { useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { authApi } from "../api";
import { AuthContext, type AuthContextValue } from "./AuthContext";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const meQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.me,
    retry: false,
  });

  const value = useMemo<AuthContextValue>(
    () => ({
      session: meQuery.data ?? null,
      isLoading: meQuery.isLoading,
      isAuthenticated: !!meQuery.data,
      refresh: async () =>
        queryClient.fetchQuery({
          queryKey: ["auth", "me"],
          queryFn: authApi.me,
        }),
      clear: () => queryClient.setQueryData(["auth", "me"], null),
    }),
    [meQuery.data, meQuery.isLoading, queryClient]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
