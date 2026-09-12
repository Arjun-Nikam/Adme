import { useState } from "react";
import { Text, TextInput, Pressable, View } from "react-native";
import { Link, Redirect, useRouter } from "expo-router";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "@/store";
import { SafeAreaView } from "react-native-safe-area-context";
import { BrandMark } from "@/components/BrandMark";
import { useLoginMutation } from "@/api/authApi";
import { loginSucceeded } from "@/store/authSlice";
import { roleHome } from "@/lib/roles";

export function LoginScreen({ audience }: { audience: "customer" | "ops" }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [login, { isLoading }] = useLoginMutation();
  const dispatch = useDispatch();
  const router = useRouter();
  const { status, role } = useSelector((state: RootState) => state.auth);
  const isCustomer = audience === "customer";

  if (status === "authenticated") return <Redirect href={roleHome(role)} />;

  async function onSubmit() {
    setError("");
    if (!username.trim() || !password) {
      setError("Enter your email, phone, or username and password.");
      return;
    }
    try {
      const response = await login({ username: username.trim(), password }).unwrap();
      dispatch(loginSucceeded({ role: response.role, name: response.name, userId: response.user_id }));
      router.replace(roleHome(response.role));
    } catch (cause) {
      const responseStatus = (cause as { status?: number }).status;
      setError(responseStatus === 401 ? "Invalid credentials." : "Could not reach the server. Check your connection.");
    }
  }

  const fieldClass = isCustomer
    ? "rounded-xl border border-nearBorder bg-nearField px-4 py-3 text-nearInk"
    : "rounded-xl border border-adminBorder bg-adminField px-4 py-3 text-adminDark";

  return (
    <SafeAreaView className={isCustomer ? "flex-1 bg-nearBg" : "flex-1 bg-adminBg"} edges={["top", "bottom"]}>
      <View className="flex-1 md:flex-row">
        <View className={isCustomer ? "flex-1 justify-between bg-nearInk px-6 py-8 md:px-12 md:py-12" : "hidden flex-1 justify-between bg-adminPrimary px-6 py-8 md:flex md:px-12 md:py-12"}>
          {isCustomer ? (
            <>
              <View>
                <Text className="text-3xl font-extrabold tracking-tight text-white">Near<Text className="text-nearAccent">Me</Text></Text>
                <Text className="mt-2 max-w-xs text-base leading-6 text-nearSoft">Good things are closer than you think.</Text>
              </View>
              <View className="max-w-sm gap-4">
                <Text className="text-4xl font-extrabold leading-tight text-white">Discover more around you.</Text>
                <Text className="text-base leading-6 text-nearSoft">Find local offers, unlock rewards, and make every nearby visit count.</Text>
                <View className="mt-4 flex-row gap-2">
                  <View className="h-2 w-12 rounded-full bg-nearAccent" />
                  <View className="h-2 w-5 rounded-full bg-nearSoft/40" />
                  <View className="h-2 w-5 rounded-full bg-nearSoft/40" />
                </View>
              </View>
            </>
          ) : (
            <>
              <BrandMark />
              <View className="max-w-sm gap-4">
                <Text className="text-4xl font-extrabold leading-tight text-white">Run the city with clarity.</Text>
                <Text className="text-base leading-6 text-adminSoft">One calm workspace for merchants, admins, and the teams moving AdMe forward.</Text>
                <Text className="pt-3 text-xs font-bold uppercase tracking-widest text-adminSoft">Merchant · Admin · Operations</Text>
              </View>
            </>
          )}
        </View>

        <View className="flex-1 justify-center px-5 py-8 md:px-12">
          <View className="w-full max-w-md self-center gap-7">
            <View className="gap-2">
              {isCustomer ? (
                <Text className="text-3xl font-extrabold text-nearInk">Welcome back</Text>
              ) : (
                <>
                  <BrandMark compact />
                  <Text className="pt-5 text-3xl font-extrabold text-adminDark">Welcome to AdMe Ops</Text>
                </>
              )}
              <Text className={isCustomer ? "text-base leading-6 text-nearMuted" : "text-base leading-6 text-adminMuted"}>
                {isCustomer ? "Sign in to discover offers and rewards near you." : "Secure access for merchant and admin teams."}
              </Text>
            </View>

            <View className={isCustomer ? "gap-3 rounded-3xl bg-nearCard p-5" : "gap-3 rounded-3xl border border-adminBorder bg-adminSurface p-5"}>
              <Text className={isCustomer ? "text-xs font-bold uppercase tracking-widest text-nearMuted" : "text-xs font-bold uppercase tracking-widest text-adminMuted"}>Account access</Text>
              <TextInput
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="email-address"
                value={username}
                onChangeText={setUsername}
                className={fieldClass}
                placeholderTextColor={isCustomer ? "#8a8174" : "#718075"}
                placeholder={isCustomer ? "Email or phone" : "merchant@adme.local"}
              />
              <Text className={isCustomer ? "pt-2 text-sm font-semibold text-nearInk" : "pt-2 text-sm font-semibold text-adminText"}>Password</Text>
              <TextInput
                secureTextEntry
                value={password}
                onChangeText={setPassword}
                onSubmitEditing={onSubmit}
                className={fieldClass}
                placeholderTextColor={isCustomer ? "#8a8174" : "#718075"}
                placeholder="Password"
              />
              {error ? <Text className="pt-1 text-sm text-red-600">{error}</Text> : null}
              <Pressable onPress={onSubmit} disabled={isLoading} className={isCustomer ? "mt-3 rounded-xl bg-nearAccent py-3.5" : "mt-3 rounded-xl bg-adminPrimary py-3.5"} style={isLoading ? { opacity: 0.6 } : undefined}>
                <Text className="text-center font-bold text-white">{isLoading ? "Signing in..." : "Sign in"}</Text>
              </Pressable>
            </View>

            {isCustomer ? (
              <View className="items-center gap-3">
                <Text className="text-nearMuted">New to NearMe?</Text>
                <Link href="/signup"><Text className="font-bold text-nearAccent">Create a customer account</Text></Link>
              </View>
            ) : (
              <View className="items-center gap-3">
                <Link href="/merchant-apply"><Text className="font-semibold text-adminPrimary">Apply as a merchant</Text></Link>
              </View>
            )}
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}