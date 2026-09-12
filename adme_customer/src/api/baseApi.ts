import { createApi } from "@reduxjs/toolkit/query/react";
import type { BaseQueryFn } from "@reduxjs/toolkit/query";
import type { AxiosError, AxiosRequestConfig } from "axios";
import { http } from "./httpClient";

/** RTK Query on top of the shared axios client (JWT + 401 refresh). */
const axiosBaseQuery =
  (): BaseQueryFn<
    {
      url: string;
      method?: AxiosRequestConfig["method"];
      data?: unknown;
      params?: unknown;
    },
    unknown,
    { status?: number; data?: unknown }
  > =>
  async ({ url, method = "GET", data, params }) => {
    try {
      const result = await http({ url, method, data, params });
      return { data: result.data };
    } catch (axiosError) {
      const err = axiosError as AxiosError;
      return {
        error: { status: err.response?.status, data: err.response?.data || err.message },
      };
    }
  };

export const baseApi = createApi({
  reducerPath: "api",
  baseQuery: axiosBaseQuery(),
  tagTypes: [
    "Me",
    "Merchant",
    "Campaign",
    "Offer",
    "Report",
    "Redemption",
    "Consumer",
    "Driver",
    "Rickshaw",
    "AuditLog",
    "AdMedia",
  ],
  endpoints: () => ({}),
});
