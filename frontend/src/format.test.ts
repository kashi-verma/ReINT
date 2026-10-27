import { describe, expect, it } from "vitest";

import { formatMw, formatPercent, formatTime } from "./format";

describe("display formatting", () => {
  it("labels missing MW values without implying zero", () => {
    expect(formatMw(null)).toBe("—");
  });

  it("formats generation with units", () => {
    expect(formatMw(5711)).toBe("5,711 MW");
  });

  it("formats coverage as a percentage", () => {
    expect(formatPercent(1)).toBe("100%");
  });

  it("displays API timestamps in UTC", () => {
    expect(formatTime("2026-01-06T07:30:00Z")).toBe("07:30");
  });
});
