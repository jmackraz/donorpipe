import type { Donation } from "../lib/graph"

interface Props {
  donations: Map<string, Donation>
}

export default function DonationList({ donations }: Props) {
  const items = [...donations.values()].sort((a, b) =>
    b.date.localeCompare(a.date)
  )

  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-800 mb-2">
        Donations ({items.length})
      </h2>
      <div className="overflow-y-auto max-h-[70vh] rounded border border-gray-200 bg-white divide-y divide-gray-100">
        {items.length === 0 ? (
          <p className="p-4 text-sm text-gray-500">No donations.</p>
        ) : (
          items.map((d) => (
            <div key={d.id} className="px-4 py-3 text-sm">
              <div className="flex justify-between">
                <span className="font-medium text-gray-900">{d.name || "—"}</span>
                <span className="text-gray-700">
                  {(d.net / 100).toFixed(2)} {d.currency.toUpperCase()}
                </span>
              </div>
              <div className="text-gray-500 flex gap-3 mt-0.5">
                <span>{d.date}</span>
                {d.designation && <span>{d.designation}</span>}
                <span className="font-mono text-xs text-gray-400">{d.id}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  )
}
