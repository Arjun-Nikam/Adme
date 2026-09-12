import { Stack } from "expo-router";
import { RoleGuard } from "@/components/RoleGuard";

export default function SuperAdminLayout() {
  return (
    <RoleGuard allow={["super_admin"]}>
      <Stack screenOptions={{ headerShown: false }} />
    </RoleGuard>
  );
}
