import { useState, type ComponentProps } from "react";
import { Pressable, Text, TextInput, View } from "react-native";
import { Card } from "@/components/Screen";
import { AppScreen } from "@/components/AppScreen";
import { useLaunchCampaignMutation } from "@/api/merchantApi";

const inputClass = "rounded-xl bg-bg px-3 py-3 text-white";

export default function MerchantCampaign() {
  const [form, setForm] = useState({
    title: "",
    start_date: new Date().toISOString().slice(0, 10),
    end_date: "",
    offer_code: "",
    offer_title: "",
    description: "",
    discount_value: "",
  });
  const [launch, result] = useLaunchCampaignMutation();
  const set = (key: keyof typeof form, value: string) =>
    setForm((current) => ({ ...current, [key]: value }));

  return (
    <AppScreen title="Merchant" subtitle="Create a live ad">
      <Card heading="Campaign">
        <Text className="text-sm text-muted">
          Active campaigns appear in the passenger feed during these dates.
        </Text>
        <Field label="Campaign title" value={form.title} onChangeText={(v) => set("title", v)} />
        <Field label="Start date (YYYY-MM-DD)" value={form.start_date} onChangeText={(v) => set("start_date", v)} />
        <Field label="End date (YYYY-MM-DD)" value={form.end_date} onChangeText={(v) => set("end_date", v)} />
      </Card>
      <Card heading="Offer shown to passengers">
        <Field label="Offer title" value={form.offer_title} onChangeText={(v) => set("offer_title", v)} />
        <Field label="Offer code" value={form.offer_code} onChangeText={(v) => set("offer_code", v)} autoCapitalize="characters" />
        <Field label="Discount value" value={form.discount_value} onChangeText={(v) => set("discount_value", v)} keyboardType="decimal-pad" />
        <Field label="Description" value={form.description} onChangeText={(v) => set("description", v)} multiline />
      </Card>
      <Pressable
        className="rounded-xl bg-primary p-4"
        disabled={result.isLoading}
        onPress={() => launch({ ...form, discount_value: form.discount_value })}
      >
        <Text className="text-center font-semibold text-white">
          {result.isLoading ? "Publishing..." : "Publish live ad"}
        </Text>
      </Pressable>
      {result.isSuccess ? (
        <Text className="text-sm text-green-400">
          Your ad is live and available in the passenger feed.
        </Text>
      ) : null}
      {result.isError ? (
        <Text className="text-sm text-red-400">
          Could not publish the ad. Check the dates, code, and discount value.
        </Text>
      ) : null}
    </AppScreen>
  );
}

function Field({
  label,
  ...props
}: { label: string } & ComponentProps<typeof TextInput>) {
  return (
    <View className="gap-1">
      <Text className="text-xs text-muted">{label}</Text>
      <TextInput className={inputClass} placeholderTextColor="#64748b" {...props} />
    </View>
  );
}
