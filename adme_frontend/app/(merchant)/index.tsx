import { Link } from "expo-router";
import { ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useSelector } from "react-redux";
import type { RootState } from "@/store";
import { Card } from "@/components/Screen";
import { DashboardHeader } from "@/components/DashboardHeader";
import { LineChartDual, BarBreakdown } from "@/components/charts/MiniCharts";
import { useMerchantDashboardQuery } from "@/api/merchantApi";

const KPI: { key: keyof Totals; label: string }[] = [
  { key: "ad_views", label: "Ad Views (Est.)" },
  { key: "qr_scans", label: "QR Scans" },
  { key: "offers_saved", label: "Offers Saved" },
  { key: "store_visits", label: "Store Visits" },
  { key: "offers_redeemed", label: "Redeemed" },
];

type Totals = {
  ad_views: number;
  qr_scans: number;
  offers_saved: number;
  store_visits: number;
  offers_redeemed: number;
};

/** Story MER-2 / MER-3 (RD 2.3) — campaign analytics dashboard. */
export default function MerchantHome() {
  const merchantId = useSelector((s: RootState) => s.auth.merchantId);
  const { data, isLoading, isError, refetch } = useMerchantDashboardQuery(
    merchantId as number,
    { skip: merchantId == null },
  );

  return (
    <SafeAreaView className="flex-1 bg-bg" edges={["top", "bottom"]}>
      <ScrollView contentContainerStyle={{ padding: 20, gap: 16 }}>
        <DashboardHeader
          title="Merchant Dashboard"
          subtitle={data?.merchant.business_name}
        />

        {merchantId == null ? (
          <Card heading="No merchant profile">
            <Text className="text-muted">
              This account isn&apos;t linked to a merchant yet. Ask Ops to
              complete onboarding (Story MER-1).
            </Text>
          </Card>
        ) : isLoading ? (
          <Card>
            <Text className="text-muted">Loading last 30 days…</Text>
          </Card>
        ) : isError ? (
          <Card heading="Couldn't load the dashboard">
            <Text className="text-muted" onPress={() => refetch()}>
              Tap to retry.
            </Text>
          </Card>
        ) : data ? (
          <>
            <View className="flex-row flex-wrap gap-3">
              {KPI.map((k) => (
                <View
                  key={k.key}
                  className="min-w-[30%] flex-1 rounded-2xl bg-surface p-3"
                >
                  <Text className="text-xs text-muted">{k.label}</Text>
                  <Text className="text-xl font-bold text-white">
                    {data.totals[k.key].toLocaleString()}
                  </Text>
                </View>
              ))}
            </View>

            <Card heading="Daily ad views vs QR scans">
              {data.time_series.length ? (
                <LineChartDual
                  series={data.time_series}
                  aKey="ad_views"
                  bKey="qr_scans"
                  aLabel="Ad views"
                  bLabel="QR scans"
                />
              ) : (
                <Text className="text-muted">No metrics in this window.</Text>
              )}
            </Card>

            <Card heading="Redemptions by time slot">
              <BarBreakdown data={data.redemption_breakdown} />
            </Card>

            <Link
              href="/(merchant)/approve"
              className="rounded-2xl bg-primary p-4"
            >
              <Text className="text-center font-semibold text-white">
                Approve a redemption (MER-5) →
              </Text>
            </Link>
            <Link
              href="/(merchant)/campaign"
              className="rounded-2xl border border-primary p-4"
            >
              <Text className="text-center font-semibold text-primary">
                Create a live ad
              </Text>
            </Link>
          </>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}
