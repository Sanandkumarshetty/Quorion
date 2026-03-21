import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { postJson } from "../lib/api";

const AuthContext = createContext(null);
const STORAGE_KEY = "quorion-auth-session";

function getStoredSession() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => getStoredSession());
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const stored = getStoredSession();

    async function validateStoredSession() {
      if (!stored?.token) {
        if (isMounted) {
          setSession(null);
          setIsBootstrapping(false);
        }
        return;
      }

      try {
        const response = await postJson("/auth/validate", { token: stored.token });
        const nextSession = { token: stored.token, user: response.user };
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
        if (isMounted) {
          setSession(nextSession);
        }
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
        if (isMounted) {
          setSession(null);
        }
      } finally {
        if (isMounted) {
          setIsBootstrapping(false);
        }
      }
    }

    validateStoredSession();

    return () => {
      isMounted = false;
    };
  }, []);

  async function login(payload) {
    const response = await postJson("/auth/login", payload);
    const nextSession = { token: response.token, user: response.user };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
    setSession(nextSession);
    return response;
  }

  async function register(payload) {
    const response = await postJson("/auth/register", payload);
    const nextSession = { token: response.token, user: response.user };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
    setSession(nextSession);
    return response;
  }

  function logout() {
    window.localStorage.removeItem(STORAGE_KEY);
    setSession(null);
  }

  const value = useMemo(
    () => ({
      session,
      user: session?.user ?? null,
      token: session?.token ?? null,
      isAuthenticated: Boolean(session?.token && session?.user),
      isBootstrapping,
      login,
      register,
      logout
    }),
    [isBootstrapping, session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
