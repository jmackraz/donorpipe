import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react"
import { useQueryClient } from "@tanstack/react-query"

// Token stored in module-level variable — not in React state — to avoid exposing
// it through re-renders or React DevTools.
let _token: string | null = null

interface AuthContextValue {
  isAuthenticated: boolean
  getToken: () => string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ""

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Only a boolean flag lives in state so React knows when to re-render.
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const queryClient = useQueryClient()

  const login = useCallback(async (username: string, password: string) => {
    const body = new URLSearchParams({ username, password })
    const res = await fetch(`${API_BASE}/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    })
    if (!res.ok) {
      throw new Error(res.status === 401 ? "Invalid username or password" : `Login failed: ${res.status}`)
    }
    const data = (await res.json()) as { access_token: string }
    _token = data.access_token
    setIsAuthenticated(true)
  }, [])

  const logout = useCallback(() => {
    _token = null
    setIsAuthenticated(false)
    queryClient.clear()
  }, [queryClient])

  const getToken = useCallback(() => _token, [])

  const value = useMemo(
    () => ({ isAuthenticated, getToken, login, logout }),
    [isAuthenticated, getToken, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
