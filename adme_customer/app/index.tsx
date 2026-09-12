import { ActivityIndicator, View } from "react-native";
import { Redirect } from "expo-router";
import { useSelector } from "react-redux";
import type { RootState } from "@/store";
import { roleHome } from "@/lib/roles";

/** Customer app entry — open directly at the NearMe sign-in screen. */
export default function Index() {
  const { status, role } = useSelector((s: RootState) => s.auth);

  if (status === "loading") {
    return (
      <View className="flex-1 items-center justify-center bg-bg">
        <ActivityIndicator />
      </View>
    );
  }
  if (status === "authenticated") return <Redirect href={roleHome(role)} />;

  return <Redirect href="/customer-login" />;
}
