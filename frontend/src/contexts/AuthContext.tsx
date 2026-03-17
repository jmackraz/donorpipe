import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react"
import { useQueryClient } from "@tanstack/react-query"

// Token and accounts stored in module-level variables — not in React state — to avoid
// exposing them through re-renders or React DevTools.
let _token: string | null = null
let _accounts: string[] = []

interface AuthContextValue {
  isAuthenticated: boolean
  accounts: string[]
  getToken: () => string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ""

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Only a boolean flag lives in state so React knows when to re-render.
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [accounts, setAccounts] = useState<string[]>([])
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
    const b64 = _token.split(".")[1]!.replace(/-/g, "+").replace(/_/g, "/")
    const payload = JSON.parse(atob(b64)) as { accounts?: string[] }
    _accounts = payload.accounts ?? []
    setAccounts(_accounts)
    setIsAuthenticated(true)
  }, [])

  const logout = useCallback(() => {
    _token = null
    _accounts = []
    setAccounts([])
    setIsAuthenticated(false)
    queryClient.clear()
  }, [queryClient])

  const getToken = useCallback(() => _token, [])

  const value = useMemo(
    () => ({ isAuthenticated, accounts, getToken, login, logout }),
    [isAuthenticated, accounts, getToken, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
