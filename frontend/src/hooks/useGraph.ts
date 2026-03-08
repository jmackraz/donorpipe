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
