import { useEffect } from "react";
import "../global.css";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { Provider, useDispatch, useSelector } from "react-redux";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { store, type RootState } from "@/store";
import { sessionRestored, profileHydrated } from "@/store/authSlice";
import { getItem, TOKEN_KEYS } from "@/lib/storage";
import { roleFromJwt, type Role } from "@/lib/roles";
import { useMeQuery } from "@/api/authApi";

/** Restore any persisted session from the stored token, then keep the store's
 *  profile ids in sync with /auth/me/. */
function SessionBootstrap({ children }: { children: React.ReactNode }) {
  const dispatch = useDispatch();
  const status = useSelector((s: RootState) => s.auth.status);

  useEffect(() => {
    (async () => {
      const [access, savedRole] = await Promise.all([
        getItem(TOKEN_KEYS.access),
        getItem(TOKEN_KEYS.role),
      ]);
      const role =
        (access ? roleFromJwt(access) : null) ?? (savedRole as Role | null);
      dispatch(sessionRestored({ role: access ? role : null }));
    })();
  }, [dispatch]);

  const { data: me } = useMeQuery(undefined, {
    skip: status !== "authenticated",
  });

  useEffect(() => {
    if (me) {
      dispatch(
        profileHydrated({
          name: me.name,
          merchantId: me.merchant_id,
          consumerId: me.consumer_id,
          driverId: me.driver_id,
        }),
      );
    }
  }, [me, dispatch]);

  return <>{children}</>;
}

export default function RootLayout() {
  return (
    <Provider store={store}>
      <SafeAreaProvider>
        <SessionBootstrap>
          <StatusBar style="light" />
          <Stack screenOptions={{ headerShown: false }} />
        </SessionBootstrap>
      </SafeAreaProvider>
    </Provider>
  );
}
