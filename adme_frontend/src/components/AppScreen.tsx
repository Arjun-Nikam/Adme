import { ReactNode } from "react";
import { ScrollView, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { DashboardHeader } from "./DashboardHeader";
import { SectionNav } from "./SectionNav";

/** Header + optional section nav + scroll. Used by the consumer screens. */
export function AppScreen({
  title,
  subtitle,
  tabs,
  children,
}: {
  title: string;
  subtitle?: string;
  tabs?: { href: string; label: string; match: string }[];
  children: ReactNode;
}) {
  return (
    <SafeAreaView className="flex-1 bg-bg" edges={["top", "bottom"]}>
      <ScrollView contentContainerStyle={{ padding: 20, gap: 16 }}>
        <DashboardHeader title={title} subtitle={subtitle} />
        {tabs ? <SectionNav tabs={tabs} /> : null}
        <View className="gap-3">{children}</View>
      </ScrollView>
    </SafeAreaView>
  );
}

export const CONSUMER_TABS = [
  { href: "/(consumer)", label: "Home", match: "/" },
  { href: "/(consumer)/scan", label: "Scan / Redeem", match: "/scan" },
  { href: "/(consumer)/near-me", label: "Near Me", match: "/near-me" },
  { href: "/(consumer)/profile", label: "Profile", match: "/profile" },
];
