import { baseApi } from "./baseApi";

export interface PlatformOverview {
  total_live_rickshaws: number;
  total_redemptions: number;
  advertiser_count: number;
  generated_at: string;
}

export interface AdvertiserRow {
  id: number;
  business_name: string;
  approval_status: "pending" | "approved" | "rejected";
  category: string | null;
  plan: string | null;
  renewal_status: "active" | "expiring_soon" | "expired";
  contract_expiry_date: string | null;
  active_campaigns: number;
  total_redemptions: number;
  spend: number;
}

export interface FleetRow {
  id: number;
  registration_number: string;
  driver_name: string | null;
  hardware_serial: string | null;
  latitude: number | null;
  longitude: number | null;
  last_ping_at: string | null;
  is_live: boolean;
}

/** Story ADM-1 — read-only Admin dashboard data. Same endpoints serve the
 *  Super Admin views. */
export const analyticsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    platformOverview: build.query<PlatformOverview, void>({
      query: () => ({ url: "/analytics/platform-overview/" }),
    }),
    advertiserDirectory: build.query<AdvertiserRow[], void>({
      query: () => ({ url: "/analytics/advertisers/" }),
    }),
    liveFleet: build.query<FleetRow[], void>({
      query: () => ({ url: "/analytics/live-fleet/" }),
    }),
  }),
});

export const {
  usePlatformOverviewQuery,
  useAdvertiserDirectoryQuery,
  useLiveFleetQuery,
} = analyticsApi;
