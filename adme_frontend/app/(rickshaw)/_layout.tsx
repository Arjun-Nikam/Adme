import { Stack } from "expo-router";
import { RoleGuard } from "@/components/RoleGuard";

export default function RickshawLayout() {
  return (
    <RoleGuard allow={["driver", "hardware", "admin", "super_admin"]}>
      <Stack screenOptions={{ headerShown: false }} />
    </RoleGuard>
  );
}
