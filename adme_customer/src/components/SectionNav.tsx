import { Text } from "react-native";
import { Link, usePathname } from "expo-router";
import { View } from "react-native";

/** Generic read-only section switcher (used by consumer + admin dashboards). */
export function SectionNav({
  tabs,
}: {
  tabs: { href: string; label: string; match: string }[];
}) {
  const path = usePathname();
  return (
    <View className="flex-row flex-wrap gap-2">
      {tabs.map((t) => {
        const active =
          t.match === "/" ? path === "/" : path.startsWith(t.match);
        return (
          <Link
            key={t.href}
            href={t.href as never}
            className={`rounded-lg px-3 py-1.5 ${
              active ? "bg-primary" : "bg-surface"
            }`}
          >
            <Text className={active ? "text-white" : "text-muted"}>
              {t.label}
            </Text>
          </Link>
        );
      })}
    </View>
  );
}
