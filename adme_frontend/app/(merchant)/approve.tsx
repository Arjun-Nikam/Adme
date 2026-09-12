import { useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";
import { ScrollView } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Card } from "@/components/Screen";
import { DashboardHeader } from "@/components/DashboardHeader";
import {
  useApproveRedemptionMutation,
  useMatchOfferMutation,
  useRejectRedemptionMutation,
} from "@/api/merchantApi";

function errText(e: unknown): string | null {
  if (e && typeof e === "object" && "data" in e) {
    const d = (e as { data?: { offer_code?: string[]; detail?: string } }).data;
    return d?.offer_code?.[0] ?? d?.detail ?? "Something went wrong.";
  }
  return null;
}

/** Story MER-5 (RD 2.6 / 2.7) — enter the consumer's offer code, match it,
 *  then Approve (or Reject) the redemption. */
export default function ApproveScreen() {
  const [code, setCode] = useState("");
  const [match, matchState] = useMatchOfferMutation();
  const [approve, approveState] = useApproveRedemptionMutation();
  const [reject, rejectState] = useRejectRedemptionMutation();

  const matched = matchState.data;
  const finalStatus =
    approveState.data?.approval_status ?? rejectState.data?.approval_status;

  async function onMatch() {
    approveState.reset();
    rejectState.reset();
    try {
      await match({ offer_code: code.trim().toUpperCase() }).unwrap();
    } catch {
      /* surfaced */
    }
  }

  return (
    <SafeAreaView className="flex-1 bg-bg" edges={["top", "bottom"]}>
      <ScrollView contentContainerStyle={{ padding: 20, gap: 16 }}>
        <DashboardHeader title="Approve redemption" subtitle="MER-5" />

        <Card heading="1 · Enter the customer's offer code">
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
            onPress={onMatch}
            disabled={matchState.isLoading || !code.trim()}
            className="mt-3 rounded-lg bg-primary py-3"
            style={
              matchState.isLoading || !code.trim() ? { opacity: 0.6 } : undefined
            }
          >
            <Text className="text-center font-semibold text-white">
              {matchState.isLoading ? "Checking…" : "Match code"}
            </Text>
          </Pressable>
          {errText(matchState.error) ? (
            <Text className="mt-2 text-red-400">
              {errText(matchState.error)}
            </Text>
          ) : null}
        </Card>

        {matched ? (
          <Card heading="2 · Verify & approve">
            <Text className="text-white">
              Match status:{" "}
              <Text className="font-bold text-green-400">
                {matched.match_status}
              </Text>
            </Text>
            <Text className="text-xs text-muted">
              Redemption #{matched.id} · consumer #{matched.consumer}
            </Text>

            {finalStatus ? (
              <Text
                className={`mt-3 font-semibold ${
                  finalStatus === "approved"
                    ? "text-green-400"
                    : "text-red-400"
                }`}
              >
                Redemption {finalStatus}.
              </Text>
            ) : (
              <View className="mt-3 flex-row gap-3">
                <Pressable
                  onPress={() => approve(matched.id)}
                  disabled={approveState.isLoading}
                  className="flex-1 rounded-lg bg-primary py-3"
                >
                  <Text className="text-center font-semibold text-white">
                    Approve
                  </Text>
                </Pressable>
                <Pressable
                  onPress={() => reject({ id: matched.id })}
                  disabled={rejectState.isLoading}
                  className="flex-1 rounded-lg bg-surface py-3"
                >
                  <Text className="text-center font-semibold text-white">
                    Reject
                  </Text>
                </Pressable>
              </View>
            )}
            {errText(approveState.error) ? (
              <Text className="mt-2 text-red-400">
                {errText(approveState.error)}
              </Text>
            ) : null}
          </Card>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}
