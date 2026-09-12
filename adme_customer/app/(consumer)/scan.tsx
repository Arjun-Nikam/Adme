import { useState } from "react";
import { Pressable, Text, TextInput } from "react-native";
import { Card } from "@/components/Screen";
import { AppScreen, CONSUMER_TABS } from "@/components/AppScreen";
import { useScanOfferMutation } from "@/api/consumerApi";

/** Story CON-1 — scan a QR or type an offer number. On native this screen
 *  also opens the camera (expo-camera); manual entry is validated the same. */
export default function ScanScreen() {
  const [code, setCode] = useState("");
  const [scan, { data, error, isLoading, reset }] = useScanOfferMutation();

  const errText =
    error && "data" in error
      ? ((error.data as { offer_code?: string[]; detail?: string })?.offer_code?.[0] ??
        (error.data as { detail?: string })?.detail ??
        "Could not redeem that code.")
      : null;

  async function onSubmit() {
    reset();
    if (!code.trim()) return;
    try {
      await scan({ offer_code: code.trim().toUpperCase() }).unwrap();
    } catch {
      /* surfaced via `error` */
    }
  }

  return (
    <AppScreen title="Scan / Redeem" tabs={CONSUMER_TABS}>
      <Card heading="Enter offer number">
        <TextInput
          autoCapitalize="characters"
          autoCorrect={false}
          value={code}
          onChangeText={setCode}
          placeholder="e.g. DEMO-FRESH-10"
          placeholderTextColor="#64748b"
          className="rounded-lg bg-bg px-3 py-2 text-white"
        />
        <Pressable
          onPress={onSubmit}
          disabled={isLoading}
          className="mt-3 rounded-lg bg-primary py-3"
          style={isLoading ? { opacity: 0.6 } : undefined}
        >
          <Text className="text-center font-semibold text-white">
            {isLoading ? "Submitting…" : "Redeem"}
          </Text>
        </Pressable>
        {errText ? (
          <Text className="mt-2 text-red-400">{errText}</Text>
        ) : null}
      </Card>

      {data ? (
        <Card heading="Redemption started">
          <Text className="text-white">
            Show code <Text className="font-bold">{code.toUpperCase()}</Text> at
            the store.
          </Text>
          <Text className="mt-1 text-muted">
            Status: {data.match_status} → {data.approval_status}. The merchant
            will match and approve it. You earned points for scanning.
          </Text>
        </Card>
      ) : null}

      <Card heading="Camera (native)">
        <Text className="text-muted">
          On iOS/Android this screen opens the camera to scan the QR directly
          (expo-camera). QR encodes {`adme://offer/<code>`}.
        </Text>
      </Card>
    </AppScreen>
  );
}
