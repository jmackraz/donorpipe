import type { DateInterval } from "../hooks/useFilters"

export interface DateRange {
  start: string // ISO date "YYYY-MM-DD", inclusive
  end: string   // ISO date "YYYY-MM-DD", inclusive
}

function parseIsoDate(dateStr: string): { year: number; month: number; day: number } {
  const [year, month, day] = dateStr.split("-").map(Number) as [number, number, number]
  return { year, month, day }
}

function formatDate(year: number, month: number, day: number): string {
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`
}

function addDays(date: Date, n: number): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + n)
}

function toIsoString(date: Date): string {
  return formatDate(date.getFullYear(), date.getMonth() + 1, date.getDate())
}

function lastDayOfMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate()
}

export function computeDateRange(dateStart: string, interval: DateInterval): DateRange {
  const { year, month, day } = parseIsoDate(dateStart)

  switch (interval) {
    case "day":
      return { start: dateStart, end: dateStart }

    case "week": {
      const d = new Date(year, month - 1, day)
      const dow = d.getDay() // 0=Sun, 1=Mon ... 6=Sat
      const offset = (dow + 6) % 7 // days back to Monday
      return {
        start: toIsoString(addDays(d, -offset)),
        end: toIsoString(addDays(d, 6 - offset)),
      }
    }

    case "month":
      return {
        start: formatDate(year, month, 1),
        end: formatDate(year, month, lastDayOfMonth(year, month)),
      }

    case "year":
      return {
        start: formatDate(year, 1, 1),
        end: formatDate(year, 12, 31),
      }
  }
}

export function advanceDate(dateStart: string, interval: DateInterval, direction: 1 | -1): string {
  const { year, month, day } = parseIsoDate(dateStart)

  switch (interval) {
    case "day": {
      const d = new Date(year, month - 1, day)
      return toIsoString(addDays(d, direction))
    }

    case "week": {
      const { start } = computeDateRange(dateStart, "week")
      const { year: sy, month: sm, day: sd } = parseIsoDate(start)
      return toIsoString(addDays(new Date(sy, sm - 1, sd), direction * 7))
    }

    case "month": {
      let newMonth = month + direction
      let newYear = year
      if (newMonth > 12) { newMonth = 1; newYear++ }
      if (newMonth < 1)  { newMonth = 12; newYear-- }
      return formatDate(newYear, newMonth, 1)
    }

    case "year":
      return formatDate(year + direction, 1, 1)
  }
}
