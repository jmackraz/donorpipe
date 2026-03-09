import { describe, test, expect } from "bun:test"
import { computeDateRange, advanceDate } from "../src/lib/dateRange"

describe("computeDateRange", () => {
  describe("day", () => {
    test("ordinary date", () => {
      expect(computeDateRange("2020-01-15", "day")).toEqual({ start: "2020-01-15", end: "2020-01-15" })
    })
    test("year-end date", () => {
      expect(computeDateRange("2020-12-31", "day")).toEqual({ start: "2020-12-31", end: "2020-12-31" })
    })
  })

  describe("week", () => {
    test("Sunday → Mon–Sun span crosses year boundary", () => {
      // Jan 5 2020 is a Sunday; week is Dec 30–Jan 5
      expect(computeDateRange("2020-01-05", "week")).toEqual({ start: "2019-12-30", end: "2020-01-05" })
    })
    test("Monday → that week", () => {
      // Jan 6 2020 is a Monday
      expect(computeDateRange("2020-01-06", "week")).toEqual({ start: "2020-01-06", end: "2020-01-12" })
    })
    test("mid-week Friday", () => {
      // Jan 10 2020 is a Friday
      expect(computeDateRange("2020-01-10", "week")).toEqual({ start: "2020-01-06", end: "2020-01-12" })
    })
    test("Sunday at end of week", () => {
      // Jan 12 2020 is a Sunday
      expect(computeDateRange("2020-01-12", "week")).toEqual({ start: "2020-01-06", end: "2020-01-12" })
    })
    test("next Monday starts new week", () => {
      // Jan 13 2020 is a Monday
      expect(computeDateRange("2020-01-13", "week")).toEqual({ start: "2020-01-13", end: "2020-01-19" })
    })
  })

  describe("month", () => {
    test("spec example: Jan 5 → full January", () => {
      expect(computeDateRange("2020-01-05", "month")).toEqual({ start: "2020-01-01", end: "2020-01-31" })
    })
    test("leap February 2020", () => {
      expect(computeDateRange("2020-02-15", "month")).toEqual({ start: "2020-02-01", end: "2020-02-29" })
    })
    test("non-leap February 2021", () => {
      expect(computeDateRange("2021-02-15", "month")).toEqual({ start: "2021-02-01", end: "2021-02-28" })
    })
    test("December", () => {
      expect(computeDateRange("2020-12-25", "month")).toEqual({ start: "2020-12-01", end: "2020-12-31" })
    })
  })

  describe("year", () => {
    test("mid-year date", () => {
      expect(computeDateRange("2020-06-15", "year")).toEqual({ start: "2020-01-01", end: "2020-12-31" })
    })
    test("Jan 1 boundary", () => {
      expect(computeDateRange("2020-01-01", "year")).toEqual({ start: "2020-01-01", end: "2020-12-31" })
    })
  })
})

describe("advanceDate", () => {
  describe("day", () => {
    test("forward across month boundary", () => {
      expect(advanceDate("2020-01-31", "day", 1)).toBe("2020-02-01")
    })
    test("backward across year boundary", () => {
      expect(advanceDate("2020-01-01", "day", -1)).toBe("2019-12-31")
    })
    test("backward to leap day", () => {
      expect(advanceDate("2020-03-01", "day", -1)).toBe("2020-02-29")
    })
  })

  describe("week", () => {
    test("forward from mid-week snaps to next Monday", () => {
      // Jan 10 is in week Jan 6–12; next week starts Jan 13
      expect(advanceDate("2020-01-10", "week", 1)).toBe("2020-01-13")
    })
    test("backward from mid-week snaps to previous Monday", () => {
      // previous week starts Dec 30
      expect(advanceDate("2020-01-10", "week", -1)).toBe("2019-12-30")
    })
    test("forward from Monday advances by 7", () => {
      expect(advanceDate("2020-01-06", "week", 1)).toBe("2020-01-13")
    })
  })

  describe("month", () => {
    test("spec example: Jan 5 → Feb 1", () => {
      expect(advanceDate("2020-01-05", "month", 1)).toBe("2020-02-01")
    })
    test("spec example: Jan 5 → Dec 1 prev year", () => {
      expect(advanceDate("2020-01-05", "month", -1)).toBe("2019-12-01")
    })
    test("forward across year boundary", () => {
      expect(advanceDate("2020-12-15", "month", 1)).toBe("2021-01-01")
    })
    test("backward across year boundary", () => {
      expect(advanceDate("2021-01-15", "month", -1)).toBe("2020-12-01")
    })
    test("forward from 1st of month", () => {
      expect(advanceDate("2020-02-01", "month", 1)).toBe("2020-03-01")
    })
  })

  describe("year", () => {
    test("forward from mid-year", () => {
      expect(advanceDate("2020-06-15", "year", 1)).toBe("2021-01-01")
    })
    test("backward from mid-year", () => {
      expect(advanceDate("2020-06-15", "year", -1)).toBe("2019-01-01")
    })
    test("backward from Jan 1", () => {
      expect(advanceDate("2020-01-01", "year", -1)).toBe("2019-01-01")
    })
  })
})
