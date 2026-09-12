import { useState, type ComponentProps } from "react";
import { Pressable, Text, TextInput, View } from "react-native";
import { Link } from "expo-router";
import * as Location from "expo-location";
import { Card, Screen } from "@/components/Screen";
import { useApplyAsMerchantMutation } from "@/api/merchantApplicationApi";

const inputClass = "rounded-xl bg-bg px-3 py-3 text-white";

export default function MerchantApply() {
  const [form, setForm] = useState({
    username: "", email: "", phone: "", password: "", business_name: "",
    contact_person: "", store_address: "", latitude: "", longitude: "",
  });
  const [locationError, setLocationError] = useState("");
  const [isLocating, setIsLocating] = useState(false);
  const [apply, result] = useApplyAsMerchantMutation();
  const set = (key: keyof typeof form, value: string) => setForm((current) => ({ ...current, [key]: value }));

  async function useCurrentLocation() {
    setLocationError("");
    setIsLocating(true);
    try {
      const permission = await Location.requestForegroundPermissionsAsync();
      if (permission.status !== "granted") {
        setLocationError("Location permission was not granted. Enter the coordinates manually.");
        return;
      }

      const position = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      const latitude = position.coords.latitude.toFixed(6);
      const longitude = position.coords.longitude.toFixed(6);
      const places = await Location.reverseGeocodeAsync({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      });
      const place = places[0];
      const address = place
        ? [place.name, place.street, place.city, place.region, place.postalCode]
            .filter(Boolean)
            .join(", ")
        : "";

      setForm((current) => ({
        ...current,
        latitude,
        longitude,
        store_address: current.store_address || address,
      }));
    } catch {
      setLocationError("Could not read your location. Enter the shop coordinates manually.");
    } finally {
      setIsLocating(false);
    }
  }

  return (
    <Screen title="Join Adme">
      <Card heading="Merchant application">
        <Text className="text-muted">Submit your business details for admin verification.</Text>
        {([
          ["username", "Username"], ["password", "Password"], ["email", "Email"], ["phone", "Phone"],
          ["business_name", "Business name"], ["contact_person", "Contact person"],
          ["store_address", "Store address"],
        ] as const).map(([key, label]) => (
          <Field key={key} label={label} value={form[key]} onChangeText={(value) => set(key, value)} secureTextEntry={key === "password"} />
        ))}
        <Pressable
          className="rounded-xl border border-primary p-3"
          onPress={useCurrentLocation}
          disabled={isLocating}
        >
          <Text className="text-center font-semibold text-primary">
            {isLocating ? "Finding shop location..." : "Use current shop location"}
          </Text>
        </Pressable>
        <Text className="text-xs text-muted">
          Stand at the shop before using this option. You can also enter coordinates manually.
        </Text>
        <View className="flex-row gap-2">
          <Field label="Latitude" value={form.latitude} onChangeText={(value) => set("latitude", value)} keyboardType="decimal-pad" />
          <Field label="Longitude" value={form.longitude} onChangeText={(value) => set("longitude", value)} keyboardType="decimal-pad" />
        </View>
        {locationError ? <Text className="text-sm text-red-400">{locationError}</Text> : null}
      </Card>
      <Pressable className="rounded-xl bg-primary p-4" disabled={result.isLoading} onPress={() => apply(form)}>
        <Text className="text-center font-semibold text-white">{result.isLoading ? "Submitting..." : "Submit application"}</Text>
      </Pressable>
      {result.isSuccess ? <Text className="text-green-400">Application submitted. Wait for Adme admin approval before signing in.</Text> : null}
      {result.isError ? <Text className="text-red-400">Could not submit application. Check your details and try again.</Text> : null}
      <Link href="/login" className="items-center"><Text className="text-primary">Back to Adme Ops sign in</Text></Link>
    </Screen>
  );
}

function Field({ label, ...props }: { label: string } & ComponentProps<typeof TextInput>) {
  return <View className="gap-1"><Text className="text-xs text-muted">{label}</Text><TextInput className={inputClass} placeholderTextColor="#64748b" {...props} /></View>;
}