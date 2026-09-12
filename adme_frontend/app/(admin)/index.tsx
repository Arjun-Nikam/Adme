import { Link } from "expo-router";
import { Text, View } from "react-native";
import { AdminCard, AdminScreen, StatCard } from "@/components/AdminScreen";
import {
  useAdvertiserDirectoryQuery,
  useLiveFleetQuery,
  usePlatformOverviewQuery,
} from "@/api/analyticsApi";

/** Story ADM-1 — read-only platform overview. Polls every 15s
 *  (docs/architecture.md §8). */
export default function AdminOverview() {
  const overview = usePlatformOverviewQuery(undefined, {
    pollingInterval: 15000,
  });
  const advertisers = useAdvertiserDirectoryQuery("approved");
  const fleet = useLiveFleetQuery(undefined, { pollingInterval: 15000 });

  const o = overview.data;

  return (
    <AdminScreen subtitle="Overview">
      <View className="gap-3 md:flex-row">
        <StatCard label="Live rickshaws" value={o?.total_live_rickshaws} />
        <StatCard label="Total redemptions" value={o?.total_redemptions} />
        <StatCard label="Approved Advertisers" value={o?.advertiser_count} />
        <StatCard label="Pending Applications" value={o?.pending_verifications} />
      </View>

      <AdminCard heading="Advertisers">
        {(advertisers.data ?? []).slice(0, 4).map((a) => (
          <View key={a.id} className="flex-row items-center justify-between py-1">
            <View>
              <Text className="font-semibold text-adminText">{a.business_name}</Text>
              <Text className="text-xs text-adminMuted">Status: {a.approval_status}</Text>
            </View>
            <Text className="text-adminMuted">
              {a.active_campaigns} live · {a.renewal_status}
            </Text>
          </View>
        ))}
        <Link href="/(admin)/advertisers" className="pt-2">
          <Text className="font-semibold text-adminPrimary">View full directory →</Text>
        </Link>
      </AdminCard>

      <AdminCard heading="Live fleet">
        {(fleet.data ?? []).slice(0, 4).map((r) => (
          <View key={r.id} className="flex-row items-center gap-2 py-1">
            <View
              style={{
                width: 8,
                height: 8,
                borderRadius: 4,
                backgroundColor: r.is_live ? "#22c55e" : "#64748b",
              }}
            />
            <Text className="font-semibold text-adminText">{r.registration_number}</Text>
            <Text className="text-adminMuted">{r.driver_name ?? "—"}</Text>
          </View>
        ))}
        <Link href="/(admin)/fleet" className="pt-2">
          <Text className="font-semibold text-adminPrimary">View live fleet →</Text>
        </Link>
      </AdminCard>

      <View className="items-center">
        <Text className="text-xs text-adminMuted">
          {overview.fulfilledTimeStamp
            ? `Updated ${new Date(
                overview.fulfilledTimeStamp,
              ).toLocaleTimeString()} · auto-refresh 15s`
            : "Connecting…"}
        </Text>
      </View>
    </AdminScreen>
  );
}
