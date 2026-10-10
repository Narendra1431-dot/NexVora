import type { ReactNode, SVGProps } from 'react';

// NexVora navigation family: a shared 24px grid, rounded outlines and tonal insets.
// Original inline vectors keep navigation independent of fonts or remote assets.
const tone = { fill: 'currentColor', fillOpacity: 0.14, stroke: 'none' };
const artwork = {
  'agent-hub': <><circle cx="12" cy="5" r="3" {...tone}/><circle cx="12" cy="5" r="3"/><path d="M12 8v4M5 16v-4h14v4"/><rect x="2" y="16" width="6" height="5" rx="1.5"/><rect x="16" y="16" width="6" height="5" rx="1.5"/></>,
  coding: <><rect x="2" y="4" width="20" height="16" rx="3" {...tone}/><rect x="2" y="4" width="20" height="16" rx="3"/><path d="m8 9-3 3 3 3m8-6 3 3-3 3m-3-8-2 10"/></>,
  dashboard: <><rect x="3" y="3" width="8" height="11" rx="2" {...tone}/><rect x="14" y="10" width="7" height="11" rx="2" {...tone}/><rect x="3" y="3" width="8" height="11" rx="2"/><rect x="14" y="3" width="7" height="4" rx="1.5"/><rect x="3" y="17" width="8" height="4" rx="1.5"/><rect x="14" y="10" width="7" height="11" rx="2"/><path d="m5.5 10 1.5-2 1.5 1"/></>,
  profile: <><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 8h18"/><path d="M5.5 18v-1a3.5 3.5 0 0 1 7 0v1" {...tone}/><circle cx="9" cy="12" r="2"/><path d="M5.5 18v-1a3.5 3.5 0 0 1 7 0v1m3-5 2-1 2 1v2c0 1.5-2 2.5-2 2.5s-2-1-2-2.5z"/></>,
  competencies: <><path d="m12 3 5 3v6l-5 3-5-3V6z" {...tone}/><path d="m12 3 5 3v6l-5 3-5-3V6zm0 12v4m-5-8-3 5m13-5 3 5"/><circle cx="3" cy="18" r="2"/><circle cx="12" cy="21" r="1.5"/><circle cx="21" cy="18" r="2"/><path d="m9.5 9 1.5 1.5 3.5-3.5"/></>,
  careers: <><circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5z" {...tone}/><path d="m15.5 8.5-2 5-5 2 2-5zM12 3v2m9 7h-2M12 21v-2m-9-7h2"/></>,
  roadmap: <><path d="M7 20h9a4 4 0 0 0 0-8H8a4 4 0 0 1 0-8h6"/><circle cx="5" cy="20" r="2" {...tone}/><circle cx="5" cy="20" r="2"/><circle cx="11" cy="12" r="2" fill="var(--color-white, white)"/><path d="M16 8V2l5 2-5 2"/><path d="M16 2v4" {...tone}/></>,
  resources: <><path d="M3 5h6a3 3 0 0 1 3 3v13a3 3 0 0 0-3-3H3z" {...tone}/><path d="M3 5h6a3 3 0 0 1 3 3v13a3 3 0 0 0-3-3H3zm9 3a3 3 0 0 1 3-3h6v13h-6a3 3 0 0 0-3 3M6 9h3m-3 4h3m6-4h3m-3 4h3"/></>,
  assessments: <><rect x="5" y="4" width="14" height="17" rx="2"/><rect x="9" y="2" width="6" height="4" rx="1" {...tone}/><rect x="9" y="2" width="6" height="4" rx="1"/><path d="m8 11 1.5 1.5L12 10m2 2h2m-8 5h8"/><path d="M8 16h8v2H8z" {...tone}/></>,
  projects: <><path d="m3 7 9-5 9 5-9 5z" {...tone}/><path d="m3 7 9-5 9 5-9 5zm0 0v10l9 5V12m9-5v6m-14-8 9 5"/><path d="m15 18 2 2 4-5"/></>,
  resume: <><path d="M5 3h10l4 4v14H5z"/><path d="M15 3v5h4M8 16h8m-8 3h5"/><circle cx="10" cy="9" r="1.5" {...tone}/><circle cx="10" cy="9" r="1.5"/><path d="M7.5 13a2.5 2.5 0 0 1 5 0m2-1 1 1 2-2"/></>,
  certificates: <><path d="M13 17H3V4h18v8M6 8h12m-12 4h5"/><circle cx="17" cy="15" r="4" {...tone}/><circle cx="17" cy="15" r="4"/><path d="m14.5 18-1 4 3.5-1.5 3.5 1.5-1-4m-4-3 1 1 2-2"/></>,
  mentor: <><path d="M4 5h12a4 4 0 0 1 4 4v6a4 4 0 0 1-4 4h-5l-5 3v-3H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" {...tone}/><path d="M12 5H6a4 4 0 0 0-4 4v6a4 4 0 0 0 4 4v3l5-3h5a4 4 0 0 0 4-4v-3m-4-9 1.5 3.5L21 5l-3.5 1.5L16 10l-1.5-3.5L11 5l3.5-1.5Z"/><path d="M6 11h5m-5 4h9"/></>,
} satisfies Record<string, ReactNode>;

export type NavigationIconName = keyof typeof artwork;

export function NavigationIcon({ name, ...props }: SVGProps<SVGSVGElement> & { name: NavigationIconName }) {
  return <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">{artwork[name]}</svg>;
}
