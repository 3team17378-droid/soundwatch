import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import type { User } from "./types";
type Auth = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};
export const AuthContext = createContext<Auth>({
  user: null,
  loading: true,
  login: async () => {},
  logout: () => {},
});
export const useAuth = () => useContext(AuthContext);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null),
    [loading, setLoading] = useState(true);
  const queryClient = useQueryClient();
  function logout() {
    sessionStorage.removeItem("soundwatch-token");
    setUser(null);
    queryClient.clear();
  }
  useEffect(() => {
    if (sessionStorage.getItem("soundwatch-token"))
      api
        .get<User>("/auth/me")
        .then((r) => setUser(r.data))
        .catch(() => logout())
        .finally(() => setLoading(false));
    else setLoading(false);
    const expire = () => logout();
    window.addEventListener("soundwatch-expired", expire);
    return () => window.removeEventListener("soundwatch-expired", expire);
  }, []);
  async function login(email: string, password: string) {
    const { data } = await api.post("/auth/login", { email, password });
    queryClient.clear();
    sessionStorage.setItem("soundwatch-token", data.access_token);
    setUser(data.user);
  }
  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
export function Guard({ admin = false }: { admin?: boolean }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="state">인증 확인 중…</div>;
  if (!user)
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  if (admin && user.role !== "ADMIN")
    return (
      <div className="state error" role="alert">
        관리자 권한이 필요합니다.
      </div>
    );
  return <Outlet />;
}
