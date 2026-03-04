"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getToken, setToken, removeToken, isLoggedIn } from "@/lib/auth";
import { login as apiLogin } from "@/lib/api";

export function useAuth() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    setLoggedIn(isLoggedIn());
    setLoading(false);
  }, []);

  const login = useCallback(
    async (username: string, password: string) => {
      const res = await apiLogin(username, password);
      setToken(res.access_token);
      setLoggedIn(true);
      router.push("/");
    },
    [router]
  );

  const logout = useCallback(() => {
    removeToken();
    setLoggedIn(false);
    router.push("/login");
  }, [router]);

  return { loggedIn, loading, login, logout };
}
