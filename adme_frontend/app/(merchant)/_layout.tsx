import { Stack } from "expo-router";
import { RoleGuard } from "@/components/RoleGuard";

export default function MerchantLayout() {
  return (
    <RoleGuard allow={["merchant", "super_admin"]}>
      <Stack screenOptions={{ headerShown: false }} />
    </RoleGuard>
  );
}
