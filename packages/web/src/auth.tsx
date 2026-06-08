import { createContext, useContext, useState, type ReactNode } from "react";
import { api } from "./api";

interface AuthState {
  loggedIn: boolean;
  email: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loggedIn, setLoggedIn] = useState(api.isLoggedIn());
  const [email, setEmail] = useState(api.getEmail());

  const value: AuthState = {
    loggedIn,
    email,
    async login(e, password) {
      await api.login(e, password);
      setLoggedIn(true);
      setEmail(api.getEmail());
    },
    async register(e, password) {
      await api.register(e, password);
    },
    async logout() {
      await api.logout();
      setLoggedIn(false);
      setEmail(null);
    },
};

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
