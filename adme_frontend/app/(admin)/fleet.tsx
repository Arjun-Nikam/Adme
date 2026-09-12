import { Text, View } from "react-native";
import { AdminScreen, AdminCard } from "@/components/AdminScreen";
import { useLiveFleetQuery } from "@/api/analyticsApi";

function ago(iso: string | null): string {
  if (!iso) return "no pings";
  const secs = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return `${secs}s ago`;
  if (secs < 3600) return `${Math.round(secs / 60)}m ago`;
  return `${Math.round(secs / 3600)}h ago`;
}

/** Story ADM-1 (RD 4.1) — active rickshaws + last known position. Read-only.
 *  Polls every 10s; feeds the RIK-2 map later. */
export default function Fleet() {
  const { data, isLoading, isError, refetch } = useLiveFleetQuery(undefined, {
    pollingInterval: 10000,
  });

  const live = (data ?? []).filter((r) => r.is_live).length;

  return (
    <AdminScreen subtitle="Live Fleet">
      {isLoading ? (
        <AdminCard><Text className="text-adminMuted">Loading fleet...</Text></AdminCard>
      ) : isError ? (
        <AdminCard heading="Couldn't load">
          <Text className="text-adminMuted" onPress={() => refetch()}>Tap to retry.</Text>
        </AdminCard>
      ) : (
        <>
          <AdminCard heading={`${live} of ${data?.length ?? 0} active rickshaws live`}>
            <Text className="text-xs text-adminMuted">&quot;Live&quot; = a GPS ping in the last 15 minutes.</Text>
          </AdminCard>
          {(data ?? []).map((r) => (
            <View key={r.id} className="flex-row items-center gap-3 rounded-2xl border border-adminBorder bg-adminSurface p-4">
              <View style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: r.is_live ? "#218b3a" : "#9aaa9d" }} />
              <View className="flex-1">
                <Text className="font-bold text-adminDark">{r.registration_number}</Text>
                <Text className="text-xs text-adminMuted">
                  {r.driver_name ?? "unassigned"}{r.hardware_serial ? ` · ${r.hardware_serial}` : ""}
                </Text>
              </View>
              <View className="items-end">
                <Text className="text-xs text-adminMuted">{ago(r.last_ping_at)}</Text>
                {r.latitude != null ? (
                  <Text className="text-[10px] text-adminMuted">{r.latitude.toFixed(3)}, {r.longitude?.toFixed(3)}</Text>
                ) : null}
              </View>
            </View>
          ))}
        </>
      )}
    </AdminScreen>
  );
}
