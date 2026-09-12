import { useEffect, useState } from "react";
import { Platform, Pressable, Text, View } from "react-native";
import * as Location from "expo-location";
import { Card } from "@/components/Screen";
import { AppScreen, CONSUMER_TABS } from "@/components/AppScreen";
import { useLazyNearMeQuery } from "@/api/consumerApi";

const RADII: (0.5 | 1 | 3)[] = [0.5, 1, 3];
// fallback (central Bengaluru) when location permission is denied
const FALLBACK = { lat: 12.9716, lng: 77.5946 };

/** Story CON-2 — offers within a chosen radius of the rider's location. */
export default function NearMe() {
  const [radius, setRadius] = useState<0.5 | 1 | 3>(1);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [denied, setDenied] = useState(false);
  const [trigger, { data, isFetching }] = useLazyNearMeQuery();

  useEffect(() => {
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== "granted") {
          setDenied(true);
          setCoords(FALLBACK);
          return;
        }
        const pos = await Location.getCurrentPositionAsync({});
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
      } catch {
        setDenied(true);
        setCoords(FALLBACK);
      }
    })();
  }, []);

  useEffect(() => {
    if (coords) trigger({ lat: coords.lat, lng: coords.lng, radius_km: radius });
  }, [coords, radius, trigger]);

  return (
    <AppScreen title="Near Me" tabs={CONSUMER_TABS}>
      <View className="flex-row gap-2">
        {RADII.map((r) => (
          <Pressable
            key={r}
            onPress={() => setRadius(r)}
            className={`rounded-lg px-3 py-1.5 ${
              r === radius ? "bg-primary" : "bg-surface"
            }`}
          >
            <Text className={r === radius ? "text-white" : "text-muted"}>
              {r < 1 ? `${r * 1000}m` : `${r}km`}
            </Text>
          </Pressable>
        ))}
      </View>

      {denied ? (
        <Text className="text-xs text-muted">
          Location unavailable{Platform.OS === "web" ? " in this browser" : ""} —
          showing offers around central Bengaluru.
        </Text>
      ) : null}

      {isFetching || !coords ? (
        <Card>
          <Text className="text-muted">Finding offers…</Text>
        </Card>
      ) : (data ?? []).length === 0 ? (
        <Card>
          <Text className="text-muted">No active offers within {radius}km.</Text>
        </Card>
      ) : (
        (data ?? []).map((o) => (
          <View key={o.offer_id} className="rounded-2xl bg-surface p-4 gap-1">
            <View className="flex-row justify-between">
              <Text className="font-semibold text-white">{o.title}</Text>
              <Text className="text-primary">{o.distance_km} km</Text>
            </View>
            <Text className="text-xs text-muted">
              {o.merchant}
              {o.category ? ` · ${o.category}` : ""} · code {o.offer_code}
            </Text>
            <Text className="text-xs text-muted">
              {o.discount_value}% off
            </Text>
          </View>
        ))
      )}
    </AppScreen>
  );
}
