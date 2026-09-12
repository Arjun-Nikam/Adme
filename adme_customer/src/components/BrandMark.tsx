import { Text, View } from "react-native";

export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <View className="flex-row items-center gap-2">
      <View className="h-10 w-10 items-center justify-center rounded-xl bg-adminPrimary">
        <Text className="text-2xl font-extrabold text-white">A</Text>
      </View>
      <View>
        <Text className="text-2xl font-extrabold tracking-tight text-adminDark">
          Ad<Text className="text-adminPrimary">Me</Text>
        </Text>
        {!compact ? (
          <Text className="text-[9px] font-semibold uppercase tracking-widest text-adminMuted">
            Your brand. Our journey.
          </Text>
        ) : null}
      </View>
    </View>
  );
}