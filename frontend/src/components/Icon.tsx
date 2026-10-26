import type { ReactNode, SVGProps } from 'react'

export type IconName = 'overview' | 'database' | 'economy' | 'prediction' | 'retention' | 'upload' | 'clean' | 'mapping' | 'menu' | 'arrow'

const paths: Record<IconName, ReactNode> = {
  overview: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
  database: <><ellipse cx="12" cy="5" rx="8" ry="3" /><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5" /><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" /></>,
  economy: <><path d="M3 3v18h18" /><path d="m7 15 4-4 3 3 6-7" /><path d="M16 7h4v4" /></>,
  prediction: <><path d="M4 19V9" /><path d="M10 19V5" /><path d="M16 19v-7" /><path d="M22 19H2" /><circle cx="16" cy="6" r="3" /></>,
  retention: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="m17 11 2 2 4-4" /></>,
  upload: <><path d="M12 3v12" /><path d="m7 8 5-5 5 5" /><path d="M5 21h14a2 2 0 0 0 2-2v-3" /><path d="M3 16v3a2 2 0 0 0 2 2" /></>,
  clean: <><path d="m3 17 6-6 4 4-6 6H3v-4Z" /><path d="m9 11 6-6 4 4-6 6" /><path d="M14 20h7" /></>,
  mapping: <><circle cx="6" cy="6" r="3" /><circle cx="18" cy="18" r="3" /><path d="M8.5 7.5 15.5 16.5" /><path d="M15 6h4v4" /><path d="M19 6 8 17" /></>,
  menu: <><path d="M4 6h16" /><path d="M4 12h16" /><path d="M4 18h16" /></>,
  arrow: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
}

export function Icon({ name, ...props }: { name: IconName } & SVGProps<SVGSVGElement>) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>
}
