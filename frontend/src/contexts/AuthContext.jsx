import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import axios from "axios";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "";
const TOKEN_KEY = "dnd_auth_token";
const USER_KEY = "dnd_auth_user";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem(USER_KEY) || "null"); } catch { return null; }
  });
  const [usage, setUsage] = useState(null);

  const _persist = (tok, usr) => {
    setToken(tok);
    setUser(usr);
    if (tok) {
      localStorage.setItem(TOKEN_KEY, tok);
      localStorage.setItem(USER_KEY, JSON.stringify(usr));
    } else {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
  };

  const register = async (email, password) => {
    const res = await axios.post(`${BACKEND}/auth/register`, { email, password });
    _persist(res.data.token, res.data.user);
    return res.data;
  };

  const login = async (email, password) => {
    const res = await axios.post(`${BACKEND}/auth/login`, { email, password });
    _persist(res.data.token, res.data.user);
    return res.data;
  };

  const logout = () => _persist(null, null);

  const refreshUsage = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${BACKEND}/billing/usage`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUsage(res.data);
    } catch {
      // non-fatal
    }
  }, [token]);

  // Patch usage from game turn response so we don't need extra round-trips
  const patchUsage = useCallback((usageInfo) => {
    if (usageInfo) setUsage(usageInfo);
  }, []);

  useEffect(() => {
    refreshUsage();
  }, [refreshUsage]);

  return (
    <AuthContext.Provider value={{ token, user, usage, register, login, logout, refreshUsage, patchUsage }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
