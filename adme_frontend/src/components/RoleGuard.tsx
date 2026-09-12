import { ReactNode } from "react";
import { View, ActivityIndicator } from "react-native";
import { Redirect } from "expo-router";
import { useSelector } from "react-redux";
import type { RootState } from "@/store";
import { roleHome, type Role } from "@/lib/roles";

/**
 * Story CORE-1 — each role route group wraps its content in this. Renders the
 * children only if the signed-in role is allowed; otherwise redirects to the
 * user's own home (or /login when anonymous).
 */
export function RoleGuard({
  allow,
  children,
}: {
  allow: Role[];
  children: ReactNode;
}) {
  const { status, role } = useSelector((s: RootState) => s.auth);

  if (status === "loading") {
    return (
      <View className="flex-1 items-center justify-center bg-bg">
        <ActivityIndicator />
      </View>
    );
  }
  if (status === "anonymous" || !role) return <Redirect href="/login" />;
  if (!allow.includes(role)) return <Redirect href={roleHome(role)} />;
  return <>{children}</>;
}
