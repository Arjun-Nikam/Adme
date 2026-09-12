import { baseApi } from "./baseApi";

export interface MerchantVerification {
  id: number;
  username: string;
  email: string;
  phone: string;
  business_name: string;
  contact_person: string;
  store_address: string;
  latitude: string;
  longitude: string;
  approval_status: "pending" | "approved" | "rejected";
}

export interface AdMedia {
  id: number;
  title: string;
  media_type: "photo" | "video";
  file: string;
  uploaded_by: number | null;
  created_at: string;
}

export const adminApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    merchantVerifications: build.query<MerchantVerification[], string | void>({
      query: (approval_status) => ({
        url: "/admin-ops/merchant-verifications/",
        params: approval_status ? { approval_status } : undefined,
      }),
      transformResponse: (response: {
        results: MerchantVerification[];
      }) => response.results,
      providesTags: ["Merchant"],
    }),
    approveMerchant: build.mutation<MerchantVerification, number>({
      query: (id) => ({
        url: `/admin-ops/merchant-verifications/${id}/approve/`,
        method: "POST",
      }),
      invalidatesTags: ["Merchant"],
    }),
    rejectMerchant: build.mutation<MerchantVerification, number>({
      query: (id) => ({
        url: `/admin-ops/merchant-verifications/${id}/reject/`,
        method: "POST",
      }),
      invalidatesTags: ["Merchant"],
    }),
    adMedia: build.query<AdMedia[], void>({
      query: () => ({ url: "/admin-ops/media/" }),
      transformResponse: (response: { results: AdMedia[] }) => response.results,
      providesTags: ["AdMedia"],
    }),
    uploadAdMedia: build.mutation<AdMedia, FormData>({
      query: (data) => ({
        url: "/admin-ops/media/",
        method: "POST",
        data,
      }),
      invalidatesTags: ["AdMedia"],
    }),
    deleteAdMedia: build.mutation<void, number>({
      query: (id) => ({
        url: `/admin-ops/media/${id}/`,
        method: "DELETE",
      }),
      invalidatesTags: ["AdMedia"],
    }),
  }),
});

export const {
  useMerchantVerificationsQuery,
  useApproveMerchantMutation,
  useRejectMerchantMutation,
  useAdMediaQuery,
  useUploadAdMediaMutation,
  useDeleteAdMediaMutation,
} = adminApi;
