import { useCallback, useEffect, useState } from "react";

const THEME_KEY = "entrenos_theme";

export function getStoredTheme() {
  try {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === "light" || stored === "dark") return stored;
  } catch {
    /* storage unavailable */
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* storage unavailable */
  }
}

export function useTheme() {
  const [theme, setTheme] = useState(getStoredTheme);
  useEffect(() => {
    applyTheme(theme);
  }, [theme]);
  const toggle = useCallback(
    () => setTheme((t) => (t === "dark" ? "light" : "dark")),
    []
  );
  return [theme, toggle];
}

export function removeStoredTheme() {
  try {
    localStorage.removeItem(THEME_KEY);
  } catch {
    /* storage unavailable */
  }
  applyTheme(
    window.matchMedia?.("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light"
  );
}