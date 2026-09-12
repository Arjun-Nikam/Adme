import { useState } from "react";
import { Link, Redirect, useRouter } from "expo-router";
import { Text, TextInput, Pressable, View } from "react-native";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "@/store";
import { Screen, Card } from "@/components/Screen";
import {
  useRequestCustomerSignupOtpMutation,
  useVerifyCustomerSignupOtpMutation,
} from "@/api/authApi";
import { loginSucceeded } from "@/store/authSlice";
import { roleHome } from "@/lib/roles";

export default function SignupScreen() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [challengeId, setChallengeId] = useState<string | null>(null);
  const [delivery, setDelivery] = useState("");
  const [error, setError] = useState("");
  const [requestOtp, { isLoading: requesting }] = useRequestCustomerSignupOtpMutation();
  const [verifyOtp, { isLoading: verifying }] = useVerifyCustomerSignupOtpMutation();
  const dispatch = useDispatch();
  const router = useRouter();
  const { status, role } = useSelector((state: RootState) => state.auth);

  if (status === "authenticated") return <Redirect href={roleHome(role)} />;

  async function submitDetails() {
    setError("");
    if (!firstName.trim() || !email.trim() || password.length < 8) {
      setError("Enter your name, a valid email, and a password of at least 8 characters.");
      return;
    }
    try {
      const response = await requestOtp({
        first_name: firstName.trim(), last_name: lastName.trim(),
        email: email.trim(), phone: phone.trim(), password,
      }).unwrap();
      setChallengeId(response.challenge_id);
      setDelivery(response.delivery);
    } catch (cause) {
      const data = (cause as { data?: { email?: string[]; detail?: string } }).data;
      setError(data?.email?.[0] || data?.detail || "Could not send your verification code.");
    }
  }

  async function verify() {
    if (!challengeId || code.length !== 6) return;
    setError("");
    try {
      const response = await verifyOtp({ challenge_id: challengeId, code }).unwrap();
      dispatch(loginSucceeded({ role: response.role, name: response.name, userId: response.user_id }));
      router.replace(roleHome(response.role));
    } catch (cause) {
      const data = (cause as { data?: { detail?: string } }).data;
      setError(data?.detail || "That code is incorrect or expired.");
    }
  }

  return (
    <Screen title="NearMe">
      <Card heading={challengeId ? "Verify your email" : "Create your customer account"}>
        {!challengeId ? (
          <>
            <Text className="text-muted">Join NearMe to discover local offers and earn rewards.</Text>
            <TextInput value={firstName} onChangeText={setFirstName} placeholder="First name" placeholderTextColor="#64748b" className="rounded-lg bg-bg px-3 py-2 text-white" />
            <TextInput value={lastName} onChangeText={setLastName} placeholder="Last name (optional)" placeholderTextColor="#64748b" className="rounded-lg bg-bg px-3 py-2 text-white" />
            <TextInput autoCapitalize="none" keyboardType="email-address" value={email} onChangeText={setEmail} placeholder="Email address" placeholderTextColor="#64748b" className="rounded-lg bg-bg px-3 py-2 text-white" />
            <TextInput keyboardType="phone-pad" value={phone} onChangeText={setPhone} placeholder="Phone (optional)" placeholderTextColor="#64748b" className="rounded-lg bg-bg px-3 py-2 text-white" />
            <TextInput secureTextEntry value={password} onChangeText={setPassword} placeholder="Password" placeholderTextColor="#64748b" className="rounded-lg bg-bg px-3 py-2 text-white" />
            <Pressable onPress={submitDetails} disabled={requesting} className="mt-2 rounded-lg bg-primary py-3" style={requesting ? { opacity: 0.6 } : undefined}>
              <Text className="text-center font-semibold text-white">{requesting ? "Sending code..." : "Continue"}</Text>
            </Pressable>
          </>
        ) : (
          <>
            <Text className="text-muted">{delivery}</Text>
            <TextInput autoFocus keyboardType="number-pad" maxLength={6} value={code} onChangeText={setCode} placeholder="6-digit code" placeholderTextColor="#64748b" className="rounded-lg bg-bg px-3 py-2 text-center text-xl tracking-widest text-white" />
            <Pressable onPress={verify} disabled={verifying || code.length !== 6} className="mt-2 rounded-lg bg-primary py-3" style={verifying || code.length !== 6 ? { opacity: 0.6 } : undefined}>
              <Text className="text-center font-semibold text-white">{verifying ? "Verifying..." : "Verify and enter NearMe"}</Text>
            </Pressable>
            <Pressable onPress={() => { setChallengeId(null); setCode(""); }}><Text className="text-center text-primary">Edit details</Text></Pressable>
          </>
        )}
        {error ? <Text className="mt-2 text-red-400">{error}</Text> : null}
      </Card>
      <View className="items-center"><Link href="/customer-login"><Text className="text-primary">Already have an account? Sign in</Text></Link></View>
    </Screen>
  );
}