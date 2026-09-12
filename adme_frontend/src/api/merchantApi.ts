import { baseApi } from "./baseApi";

export interface MerchantDashboard {
  merchant: { id: number; business_name: string };
  period: { start: string; end: string };
  totals: {
    ad_views: number;
    qr_scans: number;
    offers_saved: number;
    store_visits: number;
    offers_redeemed: number;
  };
  time_series: {
    date: string;
    ad_views: number;
    qr_scans: number;
    offers_saved: number;
    store_visits: number;
    offers_redeemed: number;
  }[];
  redemption_breakdown: { label: string; value: number }[];
}

export interface RedemptionRow {
  id: number;
  offer: number;
  consumer: number;
  match_status: "pending" | "matched" | "mismatched";
  approval_status: "pending" | "approved" | "rejected";
  approved_at: string | null;
}

export interface CampaignLaunchInput {
  title: string;
  start_date: string;
  end_date: string;
  offer_code: string;
  offer_title: string;
  description?: string;
  discount_value: string;
}

/** RD Section 2 — merchant analytics + the MER-5 approval flow. */
export const merchantApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    merchantDashboard: build.query<MerchantDashboard, number>({
      query: (merchantId) => ({
        url: `/merchants/merchants/${merchantId}/dashboard/`,
      }),
      providesTags: ["Campaign", "Report", "Redemption"],
    }),
    matchOffer: build.mutation<RedemptionRow, { offer_code: string }>({
      query: (body) => ({
        url: "/consumers/redemptions/match/",
        method: "POST",
        data: body,
      }),
      invalidatesTags: ["Redemption"],
    }),
    approveRedemption: build.mutation<RedemptionRow, number>({
      query: (id) => ({
        url: `/consumers/redemptions/${id}/approve/`,
        method: "POST",
      }),
      invalidatesTags: ["Redemption", "Campaign"],
    }),
    rejectRedemption: build.mutation<
      RedemptionRow,
      { id: number; reason?: string }
    >({
      query: ({ id, reason }) => ({
        url: `/consumers/redemptions/${id}/reject/`,
        method: "POST",
        data: { reason: reason ?? "" },
      }),
      invalidatesTags: ["Redemption"],
    }),
    launchCampaign: build.mutation<unknown, CampaignLaunchInput>({
      query: (body) => ({
        url: "/merchants/campaigns/launch/",
        method: "POST",
        data: body,
      }),
      invalidatesTags: ["Campaign", "Offer"],
    }),
  }),
});

export const {
  useMerchantDashboardQuery,
  useMatchOfferMutation,
  useApproveRedemptionMutation,
  useRejectRedemptionMutation,
  useLaunchCampaignMutation,
} = merchantApi;
