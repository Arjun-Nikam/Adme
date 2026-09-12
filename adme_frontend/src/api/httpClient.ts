import axios, { AxiosError, AxiosRequestConfig } from "axios";
import Constants from "expo-constants";
import { deleteItem, getItem, setItem, TOKEN_KEYS } from "@/lib/storage";

const baseURL =
  process.env.EXPO_PUBLIC_API_BASE_URL ||
  (Constants.expoConfig?.extra as { apiBaseUrl?: string })?.apiBaseUrl ||
  "http://localhost:8000/api/v1";

export const http = axios.create({ baseURL });

http.interceptors.request.use(async (config) => {
  const token = await getItem(TOKEN_KEYS.access);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = await getItem(TOKEN_KEYS.refresh);
  if (!refresh) return null;
  try {
    const res = await axios.post(`${baseURL}/auth/refresh/`, { refresh });
    const access = res.data.access as string;
    await setItem(TOKEN_KEYS.access, access);
    if (res.data.refresh) await setItem(TOKEN_KEYS.refresh, res.data.refresh);
    return access;
  } catch {
    await Promise.all([
      deleteItem(TOKEN_KEYS.access),
      deleteItem(TOKEN_KEYS.refresh),
      deleteItem(TOKEN_KEYS.role),
    ]);
    return null;
  }
}

http.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as AxiosRequestConfig & { _retried?: boolean };
    if (error.response?.status === 401 && original && !original._retried) {
      original._retried = true;
      refreshing = refreshing ?? refreshAccessToken();
      const access = await refreshing;
      refreshing = null;
      if (access) {
        original.headers = { ...original.headers, Authorization: `Bearer ${access}` };
        return http(original);
      }
    }
    return Promise.reject(error);
  },
);

export { baseURL };
