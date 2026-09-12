import { Text } from "react-native";
import { Screen, Card } from "@/components/Screen";

/** Stories RIK-1 / RIK-2 / RIK-4 — KYC review, live fleet map, uptime.
 *  Map SDK per docs/adr/0005-map-provider.md. Hardware devices authenticate
 *  with a per-unit key (docs/adr/0003-device-auth.md), not this login. */
export default function RickshawHome() {
  return (
    <Screen title="Rickshaw · Driver · Hardware">
      <Card heading="Driver KYC">
        <Text className="text-muted">
          Submit / review licence, RC, ID proof. A rickshaw goes active only
          after KYC is approved. (RIK-1)
        </Text>
      </Card>
      <Card heading="Live fleet map">
        <Text className="text-muted">
          Latest GPS ping per active rickshaw, refresh ~15s. (RIK-2, Phase 6)
        </Text>
      </Card>
      <Card heading="Device screen">
        <Text className="text-muted">
          Uptime heartbeat + ad playback view for the mounted hardware build.
        </Text>
      </Card>
    </Screen>
  );
}
