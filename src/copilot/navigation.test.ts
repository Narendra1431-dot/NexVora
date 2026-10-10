import { describe, expect, it } from "vitest";
import {
  isNavigationDestination,
  NAVIGATION_DESTINATIONS,
} from "./navigation";

describe("CopilotKit navigation allowlist", () => {
  it("accepts every supported application section", () => {
    for (const destination of NAVIGATION_DESTINATIONS) {
      expect(isNavigationDestination(destination)).toBe(true);
    }
  });

  it("rejects arbitrary routes and executable input", () => {
    expect(isNavigationDestination("/admin")).toBe(false);
    expect(isNavigationDestination("javascript:alert(1)")).toBe(false);
    expect(isNavigationDestination("")).toBe(false);
  });
});
