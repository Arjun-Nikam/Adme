import { Stack } from "expo-router";
import { RoleGuard } from "@/components/RoleGuard";

export default function ConsumerLayout() {
  return (
    <RoleGuard allow={["consumer", "super_admin"]}>
      <Stack screenOptions={{ headerShown: false }} />
    </RoleGuard>
  );
}
