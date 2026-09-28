import { clsx, type ClassValue } from "clsx";

/**
 * The one class-name joiner in the app.
 *
 * Conditional Tailwind classes are string concatenation the moment you do it
 * by hand, and a hand-built string breaks Tailwind's scanner as soon as a class
 * name is computed. Both halves of every class name therefore stay in the
 * source as literals.
 */
export function cn(...values: ClassValue[]): string {
  return clsx(values);
}
