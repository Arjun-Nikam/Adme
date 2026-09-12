import { ScrollView, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Card } from "@/components/Screen";
import { DashboardHeader } from "@/components/DashboardHeader";

/** Stories SUP-1 / SUP-2 — full CRUD + pricing/system config + audit log. */
export default function SuperAdminHome() {
  return (
    <SafeAreaView className="flex-1 bg-bg" edges={["top", "bottom"]}>
      <ScrollView contentContainerStyle={{ padding: 20, gap: 16 }}>
        <DashboardHeader title="Super Admin" />
        <Card heading="Users & roles (CORE-2 / SUP-1)">
          <Text className="text-muted">
            Create / edit / deactivate any user; deactivation revokes tokens.
          </Text>
        </Card>
        <Card heading="Plans, pricing & system config (SUP-2)">
          <Text className="text-muted">
            Versioned/audited — never silently overwritten.
          </Text>
        </Card>
        <Card heading="Audit log">
          <Text className="text-muted">
            Every create/update/delete/approve across the platform.
          </Text>
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
}
