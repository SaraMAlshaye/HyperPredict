/** One consistent outline icon set (24px grid, round strokes). Decorative unless `label` is given. */
const PATHS: Record<string, string> = {
  home: "M3.5 10.5 12 3.5l8.5 7V20a1 1 0 0 1-1 1H15v-6H9v6H4.5a1 1 0 0 1-1-1z",
  check: "M5 12.5 9.5 17 19 7.5",
  clipboard: "M9 4.5h6M8.5 3h7v3h-7zM7 4.5H6a1.5 1.5 0 0 0-1.5 1.5v13.5A1.5 1.5 0 0 0 6 21h12a1.5 1.5 0 0 0 1.5-1.5V6A1.5 1.5 0 0 0 18 4.5h-1M8.5 11h7M8.5 15h4.5",
  history: "M12 21a9 9 0 1 0-9-9M3 12V7.5M3 12h4.5M12 7.5V12l3 2",
  book: "M12 7.5C10.5 6 8 5 3.5 5v13c4.5 0 7 1 8.5 2.5M12 7.5C13.5 6 16 5 20.5 5v13c-4.5 0-7 1-8.5 2.5M12 7.5v13",
  heart: "M12 20s-7.5-4.6-9-9.6C2 6.9 4.3 4.5 7.1 4.5c2 0 3.6 1.1 4.9 2.9 1.3-1.8 2.9-2.9 4.9-2.9 2.8 0 5.1 2.4 4.1 5.9-1.5 5-9 9.6-9 9.6z",
  pulse: "M3 12h4l2-5.5 4 11 2.5-7.5 1.5 2H21",
  user: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4.5 20.5c1.3-3.7 4.1-5.5 7.5-5.5s6.2 1.8 7.5 5.5",
  calendar: "M5 5.5h14a1.5 1.5 0 0 1 1.5 1.5v12a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 19V7A1.5 1.5 0 0 1 5 5.5zM3.5 10h17M8 3.5v4M16 3.5v4",
  ruler: "M3.5 17.5 17.5 3.5l3 3-14 14zM7.5 13.5l2 2M10.5 10.5l2 2M13.5 7.5l2 2",
  scale: "M6.5 4h11A2.5 2.5 0 0 1 20 6.5v11a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 17.5v-11A2.5 2.5 0 0 1 6.5 4zM8 10a4 4 0 0 1 8 0M12 10l1.5-2",
  globe: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3 12h18M12 3c2.3 2.5 3.5 5.5 3.5 9s-1.2 6.5-3.5 9c-2.3-2.5-3.5-5.5-3.5-9S9.7 5.5 12 3z",
  arrowRight: "M5 12h14M13 6l6 6-6 6",
  arrowLeft: "M19 12H5M11 6l-6 6 6 6",
  alert: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7.5V13M12 16.5v.01",
  info: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v5.5M12 7.5v.01",
  trash: "M4.5 7h15M9.5 7V4.5h5V7M6.5 7l1 13h9l1-13M10 11v5M14 11v5",
  refresh: "M19.5 11A7.5 7.5 0 1 0 17.3 16.3M19.5 4.5V11H13",
  sparkle: "M12 3.5l1.9 5.1 5.1 1.9-5.1 1.9L12 17.5l-1.9-5.1L5 10.5l5.1-1.9z",
  leaf: "M5 19c0-8 5-13.5 14.5-14.5C19 14 13.5 19 5 19zM5 19c2.5-4 5.5-6.5 9-8",
  run: "M14.5 6.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM6 21l3.5-6 3 2.5V22M5 11.5l3.5-4 4.5.5 3 4 3 .5M12.5 8.5l-2.5 6",
  moon: "M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z",
  drop: "M12 3s6 6.4 6 11a6 6 0 0 1-12 0c0-4.6 6-11 6-11z",
  shaker: "M8.5 3.5h7l1.5 4h-10zM7 7.5h10v11a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2zM10.5 5.5h.01M13.5 5.5h.01",
  shield: "M12 3l7.5 3v6c0 4.7-3.2 7.9-7.5 9-4.3-1.1-7.5-4.3-7.5-9V6z",
  model: "M7.5 6h9A1.5 1.5 0 0 1 18 7.5v9a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 16.5v-9A1.5 1.5 0 0 1 7.5 6zM9.5 2.5V6M14.5 2.5V6M9.5 18v3.5M14.5 18v3.5M2.5 9.5H6M2.5 14.5H6M18 9.5h3.5M18 14.5h3.5",
  hand: "M8.5 12.5V5.5a1.5 1.5 0 0 1 3 0V11M11.5 10.5V4a1.5 1.5 0 0 1 3 0v6.5M14.5 10.5V5.5a1.5 1.5 0 0 1 3 0V12M17.5 9a1.5 1.5 0 0 1 3 0v5.5a6.5 6.5 0 0 1-6.5 6.5h-1a6.5 6.5 0 0 1-5-2.4L4.6 15.4a1.5 1.5 0 0 1 2.3-1.9l1.6 1.8",
  timer: "M12 21a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM12 9v4l2.5 1.5M9.5 2.5h5",
  plug: "M9 2.5V7M15 2.5V7M6.5 7h11v4a5.5 5.5 0 0 1-11 0zM12 16.5v5",
  stethoscope:"M6 3.5v5a4 4 0 0 0 8 0v-5M6 3.5H4.5M14 3.5h1.5M10 12.5v2.5a5 5 0 0 0 10 0v-2M20 10.5a2 2 0 1 0 0 .01",
};

export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 20, label, className }: {
  name: IconName; size?: number; label?: string; className?: string;
}) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round"
      className={className} role={label ? "img" : undefined}
      aria-label={label} aria-hidden={label ? undefined : true} focusable="false"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
