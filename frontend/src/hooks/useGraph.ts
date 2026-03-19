import { useQuery } from "@tanstack/react-query"
import { fromGraph } from "../lib/graph"
import type { TransactionStore } from "../lib/graph"
import type { EntityGraph } from "../lib/types"
import { useAuth } from "../contexts/AuthContext"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ""

async function fetchGraph(
  accountId: string,
  token: string,
  logout: () => void,
): Promise<TransactionStore> {
  const res = await fetch(`${API_BASE}/accounts/${accountId}/graph`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (res.status === 401) {
    logout()
    throw new Error("Session expired")
  }
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  const data = (await res.json()) as EntityGraph
  return fromGraph(data)
}

export function useGraph(accountId: string) {
  const { getToken, logout } = useAuth()
  return useQuery({
    queryKey: ["graph", accountId],
    queryFn: () => {
      const token = getToken()!
      return fetchGraph(accountId, token, logout)
    },
    enabled: !!accountId,
    staleTime: Infinity,
    retry: 1,
  })
}

export function useGraphMeta(accountId: string, loadedGeneratedAt?: string) {
  const { getToken, logout } = useAuth()
  const query = useQuery({
    queryKey: ["graph-meta", accountId],
    queryFn: async () => {
      const token = getToken()!
      const res = await fetch(`${API_BASE}/accounts/${accountId}/graph`, {
        method: "HEAD",
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.status === 401) { logout(); return null }
      return res.headers.get("Last-Modified")
    },
    enabled: !!accountId && !!loadedGeneratedAt,
    staleTime: 0,
    refetchInterval: (query) => {
      const serverLastModified = query.state.data
      if (loadedGeneratedAt && serverLastModified && new Date(serverLastModified) > new Date(loadedGeneratedAt)) {
        return false  // new data already detected — stop polling until user reloads
      }
      return 10_000
    },
  })
  const newDataAvailable =
    !!loadedGeneratedAt &&
    !!query.data &&
    new Date(query.data) > new Date(loadedGeneratedAt)
  return { newDataAvailable }
}
