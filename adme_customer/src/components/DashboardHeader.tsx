import { Text, View, Pressable } from "react-native";
import { useRouter } from "expo-router";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "@/store";
import { useLogoutMutation } from "@/api/authApi";
import { loggedOut } from "@/store/authSlice";

/** Shared across every dashboard: title, who's signed in, and log out. */
export function DashboardHeader({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  const { name, role } = useSelector((s: RootState) => s.auth);
  const [logout] = useLogoutMutation();
  const dispatch = useDispatch();
  const router = useRouter();

  async function onLogout() {
    await logout().unwrap();
    dispatch(loggedOut());
    router.replace("/login");
  }

  return (
    <View className="gap-4 border-b border-adminBorder pb-5">
      <View className="flex-row items-center justify-between">
        <View>
          <Text className="text-xs font-bold uppercase tracking-widest text-adminPrimary">Operations overview</Text>
          <Text className="pt-1 text-3xl font-extrabold text-adminDark">{title}</Text>
        </View>
        <Pressable
          onPress={onLogout}
          className="rounded-xl border border-adminBorder bg-adminSurface px-4 py-2.5"
        >
          <Text className="text-sm font-semibold text-adminText">Log out</Text>
        </Pressable>
      </View>
      <View className="flex-row items-center gap-2">
        {role ? (
          <Text className="rounded-full bg-adminSoft px-2.5 py-1 text-xs font-bold uppercase text-adminPrimary">
            {role}
          </Text>
        ) : null}
        <Text className="text-sm text-adminMuted">
          {name ?? "—"}
          {subtitle ? `  ·  ${subtitle}` : ""}
        </Text>
      </View>
    </View>
  );
}
