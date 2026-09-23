// Geometry of the global teacher timetable (teachers x day/hour), shared by the
// Excel export and the swaps page.

export const DAY_ORDER = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"];
export const HOUR_ORDER = [
  "08:00-09:00",
  "09:00-10:00",
  "10:00-11:00",
  "11:00-12:00",
  "12:00-13:00",
  "13:00-14:00",
];

const DAY_LABEL_TO_INDEX: Record<string, number> = {
  lunedì: 0,
  lunedi: 0,
  monday: 0,
  martedì: 1,
  martedi: 1,
  tuesday: 1,
  mercoledì: 2,
  mercoledi: 2,
  wednesday: 2,
  giovedì: 3,
  giovedi: 3,
  thursday: 3,
  venerdì: 4,
  venerdi: 4,
  friday: 4,
};

// WCAG contrast ratio of a #rrggbb background against black text.
export const contrastWithBlack = (hex: string): number => {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return (0.2126 * r + 0.7152 * g + 0.0722 * b + 0.05) / 0.05;
};

export const getDayIndex = (day: string): number | undefined => {
  const normalizedDay = day.trim().toLowerCase();
  const mappedDay = DAY_LABEL_TO_INDEX[normalizedDay];

  if (mappedDay !== undefined) {
    return mappedDay;
  }

  const numericDay = Number(normalizedDay);
  if (Number.isInteger(numericDay) && numericDay >= 0 && numericDay < DAY_ORDER.length) {
    return numericDay;
  }

  return undefined;
};

const collator = new Intl.Collator("it", { sensitivity: "base" });

export const compareTeacherNames = (first: string, second: string): number =>
  collator.compare(first, second);
