import { useState, useCallback } from "react"
import { useAuth } from "../contexts/AuthContext"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ""

export function useRequestRefresh(accountId: string) {
  const { getToken, logout } = useAuth()
  const [requestedAt, setRequestedAt] = useState<string | null>(null)

  const requestRefresh = useCallback(async () => {
    const token = getToken()
    if (!token || !accountId) return
    const res = await fetch(`${API_BASE}/accounts/${accountId}/refresh`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    })
    if (res.status === 401) { logout(); return }
    if (!res.ok) return
    const data = (await res.json()) as { requested_at: string }
    setRequestedAt(data.requested_at)
  }, [accountId, getToken, logout])

  const clearRequest = useCallback(() => setRequestedAt(null), [])

  return { requestRefresh, requestedAt, clearRequest }
}
