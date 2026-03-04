import { useQuery } from "@tanstack/react-query"
import { fromGraph } from "../lib/graph"
import type { TransactionStore } from "../lib/graph"
import type { EntityGraph } from "../lib/types"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

async function fetchGraph(accountId: string): Promise<TransactionStore> {
  const res = await fetch(`${API_BASE}/accounts/${accountId}/graph`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  const data = (await res.json()) as EntityGraph
  return fromGraph(data)
}

export function useGraph(accountId: string) {
  return useQuery({
    queryKey: ["graph", accountId],
    queryFn: () => fetchGraph(accountId),
    enabled: !!accountId,
    staleTime: Infinity,
    retry: 1,
  })
}
