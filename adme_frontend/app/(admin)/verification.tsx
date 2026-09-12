import { Pressable, Text, View } from "react-native";
import { AdminCard, AdminScreen } from "@/components/AdminScreen";
import {
  useApproveMerchantMutation,
  useMerchantVerificationsQuery,
  useRejectMerchantMutation,
} from "@/api/adminApi";

export default function MerchantVerification() {
  const { data, isLoading, isError, refetch } = useMerchantVerificationsQuery("pending");
  const [approve] = useApproveMerchantMutation();
  const [reject] = useRejectMerchantMutation();

  return (
    <AdminScreen subtitle="Merchant verification" readOnly={false}>
      {isLoading ? <Text className="text-adminMuted">Loading applications...</Text> : null}
      {isError ? (
        <AdminCard heading="Could not load applications">
          <Text className="text-adminMuted" onPress={() => refetch()}>Tap to retry.</Text>
        </AdminCard>
      ) : null}
      {(data ?? []).map((merchant) => (
        <AdminCard key={merchant.id} heading={merchant.business_name}>
          <Text className="text-adminMuted">{merchant.contact_person} · {merchant.phone || merchant.email}</Text>
          <Text className="text-adminMuted">{merchant.store_address}</Text>
          <Text className="text-xs text-adminMuted">GPS: {merchant.latitude}, {merchant.longitude}</Text>
          <View className="flex-row gap-2 pt-2">
            <Pressable className="flex-1 rounded-xl bg-adminPrimary p-3" onPress={() => approve(merchant.id)}>
              <Text className="text-center font-semibold text-white">Accept</Text>
            </Pressable>
            <Pressable className="flex-1 rounded-xl bg-red-500 p-3" onPress={() => reject(merchant.id)}>
              <Text className="text-center font-semibold text-white">Reject</Text>
            </Pressable>
          </View>
        </AdminCard>
      ))}
      {!isLoading && !isError && data?.length === 0 ? (
        <AdminCard><Text className="text-adminMuted">No merchant applications are waiting for review.</Text></AdminCard>
      ) : null}
    </AdminScreen>
  );
}