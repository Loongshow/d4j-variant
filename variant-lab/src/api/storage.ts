import type { VariantRun } from "./types";

const VARIANT_STORAGE_KEY = "d4j-variant-lab:runs";

export function readVariantRuns(): VariantRun[] {
  const raw = window.localStorage.getItem(VARIANT_STORAGE_KEY);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as VariantRun[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function writeVariantRuns(runs: VariantRun[]): void {
  window.localStorage.setItem(VARIANT_STORAGE_KEY, JSON.stringify(runs));
}
