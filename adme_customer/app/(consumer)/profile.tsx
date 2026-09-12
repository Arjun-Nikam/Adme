import { Text, View } from "react-native";
import { Card } from "@/components/Screen";
import { AppScreen, CONSUMER_TABS } from "@/components/AppScreen";
import { useMyProfileQuery } from "@/api/consumerApi";

const STATUS_COLOR: Record<string, string> = {
  approved: "#22c55e",
  pending: "#f59e0b",
  matched: "#f59e0b",
  rejected: "#ef4444",
  mismatched: "#ef4444",
};

/** Story CON-4 — profile: points balances + redemption history. */
export default function Profile() {
  const { data, isLoading, isError, refetch } = useMyProfileQuery();

  if (isLoading)
    return (
      <AppScreen title="Profile" tabs={CONSUMER_TABS}>
        <Card>
          <Text className="text-muted">Loading…</Text>
        </Card>
      </AppScreen>
    );

  if (isError || !data)
    return (
      <AppScreen title="Profile" tabs={CONSUMER_TABS}>
        <Card heading="Couldn't load">
          <Text className="text-muted" onPress={() => refetch()}>
            Tap to retry.
          </Text>
        </Card>
      </AppScreen>
    );

  return (
    <AppScreen title="Profile" tabs={CONSUMER_TABS}>
      <View className="flex-row gap-3">
        <View className="flex-1 rounded-2xl bg-surface p-4">
          <Text className="text-xs text-muted">NearMe points</Text>
          <Text className="text-2xl font-bold text-white">
            {data.adme_points_balance}
          </Text>
        </View>
        <View className="flex-1 rounded-2xl bg-surface p-4">
          <Text className="text-xs text-muted">Redemptions</Text>
          <Text className="text-2xl font-bold text-white">
            {data.totals.redemptions_approved}/{data.totals.redemptions_total}
          </Text>
        </View>
      </View>

      <Card heading="Merchant loyalty points">
        {data.merchant_points.length ? (
          data.merchant_points.map((m) => (
            <View key={m.merchant} className="flex-row justify-between py-0.5">
              <Text className="text-white">{m.merchant}</Text>
              <Text className="text-muted">{m.points} pts</Text>
            </View>
          ))
        ) : (
          <Text className="text-muted">None yet.</Text>
        )}
      </Card>

      <Card heading="History">
        {data.redemptions.map((r) => (
          <View key={r.id} className="border-b border-bg py-2">
            <View className="flex-row items-center justify-between">
              <Text className="text-white">{r.offer_title}</Text>
              <View className="flex-row items-center gap-1">
                <View
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: 4,
                    backgroundColor:
                      STATUS_COLOR[r.approval_status] ?? "#64748b",
                  }}
                />
                <Text className="text-xs text-muted">{r.approval_status}</Text>
              </View>
            </View>
            <Text className="text-xs text-muted">
              {r.merchant} · {r.discount_value}% · code {r.offer_code}
            </Text>
          </View>
        ))}
        {data.redemptions.length === 0 ? (
          <Text className="text-muted">No redemptions yet.</Text>
        ) : null}
      </Card>
    </AppScreen>
  );
}
