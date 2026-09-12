/**
 * Token storage that works on every target: expo-secure-store on native,
 * localStorage on web (SecureStore is a no-op / throws there).
 */
import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

const web = Platform.OS === "web";

export async function setItem(key: string, value: string): Promise<void> {
  if (web) {
    try {
      window.localStorage.setItem(key, value);
    } catch {
      /* private mode / SSR */
    }
    return;
  }
  await SecureStore.setItemAsync(key, value);
}

export async function getItem(key: string): Promise<string | null> {
  if (web) {
    try {
      return window.localStorage.getItem(key);
    } catch {
      return null;
    }
  }
  return SecureStore.getItemAsync(key);
}

export async function deleteItem(key: string): Promise<void> {
  if (web) {
    try {
      window.localStorage.removeItem(key);
    } catch {
      /* ignore */
    }
    return;
  }
  await SecureStore.deleteItemAsync(key);
}

export const TOKEN_KEYS = {
  access: "adme_access_token",
  refresh: "adme_refresh_token",
  role: "adme_role",
} as const;
