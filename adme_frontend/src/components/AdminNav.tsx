import { Pressable, Text, View } from "react-native";
import { router, usePathname } from "expo-router";
import { BrandMark } from "./BrandMark";

const TABS = [
  { href: "/", label: "Overview" },
  { href: "/advertisers", label: "Advertisers" },
  { href: "/media", label: "Media library" },
  { href: "/verification", label: "Merchant verification" },
  { href: "/fleet", label: "Live Fleet" },
] as const;

/** Section switcher for the Admin dashboard and merchant verification. */
export function AdminNav() {
  const pathname = usePathname();

  return (
    <View className="w-full gap-8 border-b border-adminBorder bg-adminSurface px-5 py-5 md:w-64 md:border-b-0 md:border-r md:px-4 md:py-7">
      <BrandMark />
      <View className="gap-1 md:flex-1">
        <Text className="pb-2 text-[10px] font-bold uppercase tracking-widest text-adminMuted">
          Workspace
        </Text>
        {TABS.map((t, index) => {
          const active = pathname === t.href || pathname === `/(admin)${t.href}` || (t.href === "/" && pathname === "/");
          return (
            <Pressable
              key={t.href}
              onPress={() => router.push(`/(admin)${t.href}`)}
              className={`flex-row items-center gap-3 rounded-xl px-3 py-3 ${active ? "bg-adminSoft" : ""}`}
            >
              <View className={`h-7 w-7 items-center justify-center rounded-lg ${active ? "bg-adminPrimary" : "bg-adminBg"}`}>
                <Text className={`text-xs font-bold ${active ? "text-white" : "text-adminMuted"}`}>
                  {index === 0 ? "⌂" : index === 1 ? "◉" : index === 2 ? "✓" : "▣"}
                </Text>
              </View>
              <Text className={`font-semibold ${active ? "text-adminPrimary" : "text-adminText"}`}>
                {t.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
      <View className="hidden rounded-xl bg-adminSoft p-3 md:flex">
        <Text className="text-xs font-bold text-adminDark">AdMe operations</Text>
        <Text className="pt-1 text-[11px] leading-4 text-adminMuted">Monitor campaigns, media, and fleet activity in one place.</Text>
      </View>
    </View>
  );
}
