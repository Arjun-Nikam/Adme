import { baseApi } from "./baseApi";

export interface Redemption {
  id: number;
  offer: number;
  merchant: number;
  match_status: "pending" | "matched" | "mismatched";
  approval_status: "pending" | "approved" | "rejected";
  approved_at: string | null;
  created_at: string;
}

export interface RedemptionSummary {
  id: number;
  offer_code: string;
  offer_title: string;
  merchant: string;
  discount_value: number;
  match_status: string;
  approval_status: string;
  store_visit_confirmed: boolean;
  created_at: string;
  approved_at: string | null;
}

export interface ConsumerProfile {
  consumer_id: number;
  adme_points_balance: number;
  merchant_points: { merchant: string; points: number }[];
  totals: { redemptions_total: number; redemptions_approved: number };
  redemptions: RedemptionSummary[];
}

export interface NearbyOffer {
  offer_id: number;
  offer_code: string;
  title: string;
  discount_value: number;
  merchant: string;
  category: string | null;
  distance_km: number;
}

export interface LiveCampaign {
  id: number;
  title: string;
  start_date: string;
  end_date: string;
  merchant: string;
  offers: {
    id: number;
    offer_code: string;
    title: string;
    description: string;
    discount_value: string;
  }[];
}

/** RD Section 3 — consumer redemption flow. */
export const consumerApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    scanOffer: build.mutation<
      Redemption,
      { offer_code: string; latitude?: number; longitude?: number }
    >({
      query: (body) => ({
        url: "/consumers/redemptions/scan/",
        method: "POST",
        data: body,
      }),
      invalidatesTags: ["Redemption", "Consumer"],
    }),
    myProfile: build.query<ConsumerProfile, void>({
      query: () => ({ url: "/consumers/consumers/me/" }),
      providesTags: ["Consumer", "Redemption"],
    }),
    nearMe: build.query<
      NearbyOffer[],
      { lat: number; lng: number; radius_km: 0.5 | 1 | 3 }
    >({
      query: ({ lat, lng, radius_km }) => ({
        url: "/merchants/offers/near-me/",
        params: { lat, lng, radius_km },
      }),
    }),
      liveCampaigns: build.query<LiveCampaign[], void>({
        query: () => ({ url: "/merchants/campaigns/live/" }),
        providesTags: ["Campaign", "Offer"],
      }),
  }),
});

  export const {
    useScanOfferMutation,
    useMyProfileQuery,
    useLazyNearMeQuery,
    useLiveCampaignsQuery,
  } = consumerApi;
