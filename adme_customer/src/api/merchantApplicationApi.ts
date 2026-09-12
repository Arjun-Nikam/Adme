import { baseApi } from "./baseApi";

export interface MerchantApplicationInput {
  username: string;
  email?: string;
  phone?: string;
  password: string;
  business_name: string;
  contact_person: string;
  store_address: string;
  latitude: string;
  longitude: string;
  category?: number | null;
  plan?: number | null;
  contract_expiry_date?: string | null;
}

export const merchantApplicationApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    applyAsMerchant: build.mutation<
      { merchant_id: number; approval_status: string; message: string },
      MerchantApplicationInput
    >({
      query: (body) => ({
        url: "/merchants/merchants/apply/",
        method: "POST",
        data: body,
      }),
    }),
  }),
});

export const { useApplyAsMerchantMutation } = merchantApplicationApi;