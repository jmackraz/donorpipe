#!/usr/bin/env bun
/**
 * Fetch and display the transaction graph from the DonorPipe API.
 *
 * Usage:
 *   bun frontend/scripts/fetch_graph.ts --account my_org
 *   bun frontend/scripts/fetch_graph.ts --account my_org --json
 *   bun frontend/scripts/fetch_graph.ts --account my_org --base-url http://localhost:8000
 */

import { fromGraph } from "../src/lib/graph"
import type { EntityGraph } from "../src/lib/types"

function parseArgs() {
  const args = process.argv.slice(2)
  let account: string | null = null
  let baseUrl = "http://localhost:8000"
  let printJson = false

  for (let i = 0; i < args.length; i++) {
    const arg = args[i]
    if (arg === "--account" && args[i + 1]) {
      account = args[++i]!
    } else if (arg === "--base-url" && args[i + 1]) {
      baseUrl = args[++i]!
    } else if (arg === "--json") {
      printJson = true
    } else if (arg === "--help" || arg === "-h") {
      console.log("Usage: bun fetch_graph.ts --account <id> [--base-url <url>] [--json]")
      process.exit(0)
    }
  }

  if (!account) {
    console.error("error: --account is required")
    process.exit(1)
  }

  return { account, baseUrl, printJson }
}

const { account, baseUrl, printJson } = parseArgs()
const url = `${baseUrl}/accounts/${account}/graph`

console.error(`GET ${url}`)

const response = await fetch(url)
if (!response.ok) {
  console.error(`error: ${response.status} ${response.statusText}`)
  process.exit(1)
}

const data = (await response.json()) as EntityGraph
const store = fromGraph(data)

if (printJson) {
  console.log(JSON.stringify(data, null, 2))
} else {
  console.log(`  donations: ${store.donations.size}`)
  console.log(`  charges:   ${store.charges.size}`)
  console.log(`  payouts:   ${store.payouts.size}`)
  console.log(`  receipts:  ${store.receipts.size}`)
}
