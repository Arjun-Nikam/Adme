import { Text, View } from "react-native";
import { Card } from "@/components/Screen";
import { AppScreen, CONSUMER_TABS } from "@/components/AppScreen";
import { useMyProfileQuery } from "@/api/consumerApi";
import { useLiveCampaignsQuery } from "@/api/consumerApi";

/** RD Section 3 — consumer home. */
export default function ConsumerHome() {
  const { data } = useMyProfileQuery();
  const campaigns = useLiveCampaignsQuery();

  return (
    <AppScreen title="NearMe" tabs={CONSUMER_TABS}>
      <Card heading="NearMe points">
        <Text className="text-3xl font-bold text-white">
          {data?.adme_points_balance ?? "…"}
        </Text>
        <Text className="text-xs text-muted">
          Earned for scanning, redeeming and engaging. Usable platform-wide.
        </Text>
      </Card>
      <Card heading="How it works">
        <Text className="text-muted">
          1· Scan a rickshaw-screen QR or type the offer number.{"\n"}
          2· Show the code at the store — the merchant matches and approves it.
          {"\n"}
          3· Your discount + loyalty points are applied.
        </Text>
      </Card>
      <Card heading="Live offers near you">
        {(campaigns.data ?? []).map((campaign) => (
          <View key={campaign.id} className="gap-1 border-b border-line pb-3">
            <Text className="font-semibold text-white">{campaign.title}</Text>
            <Text className="text-xs text-muted">{campaign.merchant}</Text>
            {campaign.offers.map((offer) => (
              <View key={offer.id} className="rounded-xl bg-bg p-3">
                <Text className="text-primary">{offer.title}</Text>
                <Text className="text-sm text-muted">
                  {offer.description || "Show this offer code at the store."}
                </Text>
                <Text className="text-xs font-semibold text-white">
                  Code: {offer.offer_code} · Discount {offer.discount_value}
                </Text>
              </View>
            ))}
          </View>
        ))}
        {campaigns.data && campaigns.data.length === 0 ? (
          <Text className="text-muted">No live offers right now.</Text>
        ) : null}
      </Card>
      <Card heading="Recent activity">
        {(data?.redemptions ?? []).slice(0, 3).map((r) => (
          <Text key={r.id} className="py-0.5 text-muted">
            {r.offer_title} · {r.merchant} · {r.approval_status}
          </Text>
        ))}
        {data && data.redemptions.length === 0 ? (
          <Text className="text-muted">Nothing yet — try Scan / Redeem.</Text>
        ) : null}
      </Card>
    </AppScreen>
  );
}
