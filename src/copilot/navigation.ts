export const NAVIGATION_DESTINATIONS = [
  "coding",
  "certificates",
  "dashboard",
  "profile",
  "competencies",
  "careers",
  "roadmap",
  "resources",
  "assessments",
  "projects",
  "resume",
  "mentor",
  "agent-hub",
] as const;

export type NavigationDestination = (typeof NAVIGATION_DESTINATIONS)[number];

export function isNavigationDestination(
  value: string,
): value is NavigationDestination {
  return (NAVIGATION_DESTINATIONS as readonly string[]).includes(value);
}
