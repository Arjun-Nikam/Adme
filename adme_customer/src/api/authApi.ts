import { baseApi } from "./baseApi";
import { setItem, deleteItem, TOKEN_KEYS } from "@/lib/storage";
import type { Role } from "@/lib/roles";

interface LoginResponse {
  access: string;
  refresh: string;
  role: Role;
  name: string;
  user_id: number;
}

export type CustomerSignupRequest = {
  first_name: string;
  last_name?: string;
  email: string;
  phone?: string;
  password: string;
};

interface SignupChallengeResponse {
  challenge_id: string;
  delivery: string;
  expires_in_seconds: number;
}

export interface MeResponse {
  id: number;
  username: string;
  name: string;
  email: string;
  phone: string;
  role: Role;
  is_active: boolean;
  merchant_id: number | null;
  consumer_id: number | null;
  driver_id: number | null;
}

export const authApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    login: build.mutation<LoginResponse, { username: string; password: string }>({
      query: (body) => ({ url: "/auth/login/", method: "POST", data: body }),
      async onQueryStarted(_arg, { queryFulfilled }) {
        const { data } = await queryFulfilled;
        await Promise.all([
          setItem(TOKEN_KEYS.access, data.access),
          setItem(TOKEN_KEYS.refresh, data.refresh),
          setItem(TOKEN_KEYS.role, data.role),
        ]);
      },
      invalidatesTags: ["Me"],
    }),
    requestCustomerSignupOtp: build.mutation<SignupChallengeResponse, CustomerSignupRequest>({
      query: (body) => ({ url: "/auth/signup/request-otp/", method: "POST", data: body }),
    }),
    verifyCustomerSignupOtp: build.mutation<LoginResponse, { challenge_id: string; code: string }>({
      query: (body) => ({ url: "/auth/signup/verify-otp/", method: "POST", data: body }),
      async onQueryStarted(_arg, { queryFulfilled }) {
        const { data } = await queryFulfilled;
        await Promise.all([
          setItem(TOKEN_KEYS.access, data.access),
          setItem(TOKEN_KEYS.refresh, data.refresh),
          setItem(TOKEN_KEYS.role, data.role),
        ]);
      },
      invalidatesTags: ["Me"],
    }),
    me: build.query<MeResponse, void>({
      query: () => ({ url: "/auth/me/" }),
      providesTags: ["Me"],
    }),
    logout: build.mutation<null, void>({
      queryFn: async () => {
        await Promise.all([
          deleteItem(TOKEN_KEYS.access),
          deleteItem(TOKEN_KEYS.refresh),
          deleteItem(TOKEN_KEYS.role),
        ]);
        return { data: null };
      },
      invalidatesTags: ["Me"],
    }),
  }),
});

export const {
  useLoginMutation,
  useRequestCustomerSignupOtpMutation,
  useVerifyCustomerSignupOtpMutation,
  useMeQuery,
  useLogoutMutation,
} = authApi;
