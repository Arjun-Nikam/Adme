import { ReactNode } from "react";
import { ScrollView, View, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

/** Standard page shell — safe area + scroll + title. */
export function Screen({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <SafeAreaView className="flex-1 bg-bg" edges={["top", "bottom"]}>
      <ScrollView contentContainerStyle={{ padding: 20, gap: 16 }}>
        <Text className="text-2xl font-bold text-white">{title}</Text>
        <View className="gap-4">{children}</View>
      </ScrollView>
    </SafeAreaView>
  );
}

export function Card({
  heading,
  children,
}: {
  heading?: string;
  children?: ReactNode;
}) {
  return (
    <View className="gap-2 rounded-2xl bg-surface p-4">
      {heading ? (
        <Text className="text-base font-semibold text-white">{heading}</Text>
      ) : null}
      {children}
    </View>
  );
}
