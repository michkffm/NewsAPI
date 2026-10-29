import { createContext, useContext } from 'react';
export const Preferences = createContext(null);
export function usePreferences() { return useContext(Preferences); }
export function readLocal(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
export function writeLocal(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch { return false; }
}
