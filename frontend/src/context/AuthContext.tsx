import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, type AuthUser } from "../api";

const TOKEN_KEY = "inventory_auth_token";
const USER_KEY = "inventory_auth_user";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredAuth(): { token: string | null; user: AuthUser | null } {
  const token = localStorage.getItem(TOKEN_KEY);
  const raw = localStorage.getItem(USER_KEY);
  if (!token || !raw) return { token: null, user: null };
  try {
    return { token, user: JSON.parse(raw) as AuthUser };
  } catch {
    return { token: null, user: null };
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const stored = readStoredAuth();
  const [user, setUser] = useState<AuthUser | null>(stored.user);
  const [token, setToken] = useState<string | null>(stored.token);
  const [isLoading, setIsLoading] = useState(Boolean(stored.token));

  const persist = useCallback((nextToken: string, nextUser: AuthUser) => {
    localStorage.setItem(TOKEN_KEY, nextToken);
    localStorage.setItem(USER_KEY, JSON.stringify(nextUser));
    setToken(nextToken);
    setUser(nextUser);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    const initialToken = localStorage.getItem(TOKEN_KEY);
    if (!initialToken) {
      setIsLoading(false);
      return;
    }

    api
      .getMe(initialToken)
      .then((me) => {
        setUser(me);
        localStorage.setItem(USER_KEY, JSON.stringify(me));
      })
      .catch(() => logout())
      .finally(() => setIsLoading(false));
  }, [logout]);

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await api.login(email, password);
      persist(result.access_token, result.user);
    },
    [persist]
  );

  const register = useCallback(
    async (fullName: string, email: string, password: string) => {
      const result = await api.register(fullName, email, password);
      persist(result.access_token, result.user);
    },
    [persist]
  );

  const value = useMemo(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated: Boolean(token && user),
      login,
      register,
      logout,
    }),
    [user, token, isLoading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
