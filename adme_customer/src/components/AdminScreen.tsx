import { ReactNode } from "react";
import { ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { DashboardHeader } from "./DashboardHeader";
import { AdminNav } from "./AdminNav";

/** Shared shell for every Admin section — header, nav, and scroll. */
export function AdminScreen({
  subtitle,
  readOnly = true,
  children,
}: {
  subtitle: string;
  readOnly?: boolean;
  children: ReactNode;
}) {
  return (
    <SafeAreaView className="flex-1 bg-adminBg" edges={["top", "bottom"]}>
      <View className="flex-1 md:flex-row">
        <AdminNav />
        <ScrollView className="flex-1" contentContainerStyle={{ padding: 24, gap: 22 }}>
          <View className="w-full max-w-6xl self-center gap-5">
            <DashboardHeader
              title={subtitle}
              subtitle={readOnly ? `${subtitle} · read-only` : subtitle}
            />
            <View className="gap-4">{children}</View>
          </View>
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}

export function StatCard({
  label,
  value,
}: {
  label: string;
  value: number | string | undefined;
}) {
  return (
    <View className="min-w-[180px] flex-1 rounded-2xl border border-adminBorder bg-adminSurface p-5">
      <Text className="text-xs font-semibold uppercase tracking-wide text-adminMuted">{label}</Text>
      <Text className="pt-2 text-3xl font-extrabold text-adminDark">
        {typeof value === "number" ? value.toLocaleString() : (value ?? "…")}
      </Text>
    </View>
  );
}

export function AdminCard({
  heading,
  children,
}: {
  heading?: string;
  children?: ReactNode;
}) {
  return (
    <View className="gap-3 rounded-2xl border border-adminBorder bg-adminSurface p-5">
      {heading ? <Text className="text-base font-bold text-adminDark">{heading}</Text> : null}
      {children}
    </View>
  );
}
