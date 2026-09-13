import { useState } from "react";
import { Alert, Image, Linking, Pressable, Text, TextInput, View } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { AdminCard, AdminScreen } from "@/components/AdminScreen";
import { useAdvertiserDirectoryQuery } from "@/api/analyticsApi";
import {
  useAdvertiserDetailQuery,
  useDeleteAdMediaMutation,
  useUploadAdMediaMutation,
  type AdMedia,
  type AdvertiserDetail,
} from "@/api/adminApi";
import { baseURL } from "@/api/httpClient";

const STATUS_COLOR: Record<string, string> = {
  active: "#22c55e",
  expiring_soon: "#f59e0b",
  expired: "#ef4444",
};

const APPROVAL_COLOR: Record<string, string> = {
  approved: "#22c55e",
  pending: "#f59e0b",
  rejected: "#ef4444",
};

const APPROVAL_BG: Record<string, string> = {
  approved: "rgba(34, 197, 94, 0.12)",
  pending: "rgba(245, 158, 11, 0.12)",
  rejected: "rgba(239, 68, 68, 0.12)",
};

const RICKSHAW_STATUS_COLOR: Record<string, string> = {
  active: "#22c55e",
  inactive: "#94a3b8",
};

function fileUrl(file: string) {
  return file.startsWith("http")
    ? file
    : `${baseURL.replace(/\/api\/v1\/?$/, "")}${file.startsWith("/") ? "" : "/"}${file}`;
}

export default function Advertisers() {
  const [statusFilter, setStatusFilter] = useState<"approved" | "pending" | "rejected" | "all">("approved");
  const { data, isLoading, isError, refetch } = useAdvertiserDirectoryQuery(statusFilter);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const detail = useAdvertiserDetailQuery(selectedId ?? 0, {
    skip: selectedId === null,
  });

  const [upload, { isLoading: isUploading }] = useUploadAdMediaMutation();
  const [removeMedia] = useDeleteAdMediaMutation();

  async function uploadMedia(mediaType: "photo" | "video", title: string) {
    if (selectedId === null) return;
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: mediaType === "photo" ? ["images"] : ["videos"],
      quality: 1,
    });
    if (result.canceled || !result.assets[0]) return;
    const asset = result.assets[0];
    const blob = await (await fetch(asset.uri)).blob();
    const formData = new FormData();
    formData.append("title", title.trim() || asset.fileName || `${mediaType} upload`);
    formData.append("media_type", mediaType);
    formData.append("merchant", String(selectedId));
    formData.append("file", blob, asset.fileName || `${mediaType}-${Date.now()}`);
    try {
      await upload(formData).unwrap();
      detail.refetch();
    } catch {
      Alert.alert("Upload failed", "The advertiser media could not be uploaded.");
    }
  }

  async function handleDeleteMedia(media: AdMedia) {
    Alert.alert(
      "Delete media",
      `Are you sure you want to delete "${media.title}"? This cannot be undone.`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await removeMedia(media.id).unwrap();
              detail.refetch();
            } catch {
              Alert.alert("Delete failed", "The media could not be deleted.");
            }
          },
        },
      ],
    );
  }

  const filteredData = (data ?? []).filter((advertiser) => {
    if (statusFilter === "all") return true;
    return advertiser.approval_status === statusFilter;
  });

  // ── SEPARATE ADVERTISER PROFILE VIEW MODE ────────────────────────────
  if (selectedId !== null) {
    const selectedSummary = (data ?? []).find((a) => a.id === selectedId);
    return (
      <AdminScreen subtitle={`Advertiser Profile`}>
        {/* Back Button Header */}
        <View className="flex-row items-center justify-between pb-2">
          <Pressable
            className="flex-row items-center gap-2 rounded-xl border border-adminBorder bg-adminSurface px-4 py-2.5 shadow-sm"
            onPress={() => setSelectedId(null)}
          >
            <Text className="text-base font-bold text-adminPrimary">← Back to Directory</Text>
          </Pressable>

          {selectedSummary ? (
            <View
              className="rounded-full px-3 py-1 border"
              style={{
                backgroundColor: APPROVAL_BG[selectedSummary.approval_status] ?? "rgba(148, 163, 184, 0.12)",
                borderColor: APPROVAL_COLOR[selectedSummary.approval_status] ?? "#64748b",
              }}
            >
              <Text
                className="text-xs font-bold capitalize"
                style={{ color: APPROVAL_COLOR[selectedSummary.approval_status] ?? "#64748b" }}
              >
                ● {selectedSummary.approval_status}
              </Text>
            </View>
          ) : null}
        </View>

        {/* Profile Content */}
        <AdvertiserProfileView
          selectedSummary={selectedSummary}
          detail={detail}
          isUploading={isUploading}
          onUpload={uploadMedia}
          onDeleteMedia={handleDeleteMedia}
          onBack={() => setSelectedId(null)}
        />
      </AdminScreen>
    );
  }

  // ── DIRECTORY LIST VIEW MODE ──────────────────────────────────────────
  return (
    <AdminScreen subtitle="Advertisers Directory">
      {/* Filter Tabs */}
      <View className="flex-row flex-wrap items-center justify-between gap-2 pb-2">
        <View className="flex-row gap-2">
          {(["approved", "pending", "rejected", "all"] as const).map((tab) => {
            const isActive = statusFilter === tab;
            return (
              <Pressable
                key={tab}
                onPress={() => setStatusFilter(tab)}
                className={`rounded-full px-4 py-2 border ${
                  isActive
                    ? "bg-adminPrimary border-adminPrimary"
                    : "bg-adminSurface border-adminBorder"
                }`}
              >
                <Text
                  className={`text-xs font-bold capitalize ${
                    isActive ? "text-white" : "text-adminMuted"
                  }`}
                >
                  {tab}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <Text className="text-xs font-semibold text-adminMuted">
          Showing {filteredData.length} merchant{filteredData.length === 1 ? "" : "s"}
        </Text>
      </View>

      {isLoading ? (
        <AdminCard>
          <Text className="text-adminMuted">Loading directory...</Text>
        </AdminCard>
      ) : null}

      {isError ? (
        <AdminCard heading="Couldn't load directory">
          <Text className="text-adminMuted" onPress={() => refetch()}>
            Tap to retry.
          </Text>
        </AdminCard>
      ) : null}

      {!isLoading && !isError && filteredData.length === 0 ? (
        <AdminCard>
          <Text className="text-adminMuted">No {statusFilter} advertisers found.</Text>
        </AdminCard>
      ) : null}

      <View className="gap-4">
        {filteredData.map((advertiser) => (
          <View
            key={advertiser.id}
            className="gap-3 rounded-2xl border border-adminBorder bg-adminSurface p-5 shadow-sm"
          >
            <View className="flex-row items-start justify-between">
              <View className="gap-1 flex-1 pr-2">
                <Text className="text-lg font-bold text-adminDark">
                  {advertiser.business_name}
                </Text>

                <View className="flex-row items-center gap-2 pt-1">
                  <View
                    className="rounded-md px-2 py-0.5"
                    style={{ backgroundColor: APPROVAL_BG[advertiser.approval_status] }}
                  >
                    <Text
                      className="text-xs font-bold capitalize"
                      style={{ color: APPROVAL_COLOR[advertiser.approval_status] }}
                    >
                      ● {advertiser.approval_status}
                    </Text>
                  </View>

                  <View className="flex-row items-center gap-1">
                    <View
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: STATUS_COLOR[advertiser.renewal_status] ?? "#64748b",
                      }}
                    />
                    <Text className="text-xs font-medium text-adminMuted">
                      {advertiser.renewal_status}
                    </Text>
                  </View>
                </View>
              </View>

              {/* View Profile Action Button */}
              <Pressable
                className="rounded-xl bg-adminPrimary px-4 py-2.5 shadow-sm"
                onPress={() => setSelectedId(advertiser.id)}
              >
                <Text className="text-xs font-bold text-white">View Profile & Media →</Text>
              </Pressable>
            </View>

            <Text className="text-xs text-adminMuted">
              Category: <Text className="font-semibold text-adminDark">{advertiser.category ?? "Uncategorized"}</Text> · Plan: <Text className="font-semibold text-adminDark">{advertiser.plan ?? "Custom / No Plan"}</Text>
              {advertiser.contract_expiry_date ? ` · Expiry: ${advertiser.contract_expiry_date}` : ""}
            </Text>

            <View className="flex-row gap-4 border-t border-adminBorder/60 pt-3">
              <Metric label="Live Campaigns" value={advertiser.active_campaigns} />
              <Metric label="Redemptions" value={advertiser.total_redemptions} />
              <Metric label="Total Spend" value={`₹${advertiser.spend.toLocaleString()}`} />
            </View>
          </View>
        ))}
      </View>
    </AdminScreen>
  );
}

/* ── SEPARATE DEDICATED ADVERTISER PROFILE VIEW ──────────────────────── */

function AdvertiserProfileView({
  selectedSummary,
  detail,
  isUploading,
  onUpload,
  onDeleteMedia,
  onBack,
}: {
  selectedSummary?: {
    id: number;
    business_name: string;
    approval_status: string;
    category: string | null;
    plan: string | null;
    renewal_status: string;
    active_campaigns: number;
    total_redemptions: number;
    spend: number;
  };
  detail: { isLoading: boolean; isError?: boolean; data?: AdvertiserDetail };
  isUploading: boolean;
  onUpload: (type: "photo" | "video", title: string) => void;
  onDeleteMedia: (media: AdMedia) => void;
  onBack: () => void;
}) {
  const [mediaTitle, setMediaTitle] = useState("");

  if (detail.isLoading) {
    return (
      <AdminCard>
        <Text className="py-4 text-center text-adminMuted">
          Loading advertiser profile data...
        </Text>
      </AdminCard>
    );
  }

  if (detail.isError || !detail.data) {
    return (
      <AdminCard heading="Error Loading Profile">
        <Text className="text-adminMuted">
          Could not load details for this advertiser. Please try again.
        </Text>
        <Pressable className="mt-2 rounded-xl bg-adminPrimary p-3" onPress={onBack}>
          <Text className="text-center font-bold text-white">Back to Directory</Text>
        </Pressable>
      </AdminCard>
    );
  }

  const advertiser = detail.data;

  return (
    <View className="gap-5">
      {/* 1. Header Profile Banner */}
      <View className="gap-4 rounded-2xl border border-adminBorder bg-adminSurface p-6 shadow-sm">
        <View className="flex-row flex-wrap items-start justify-between gap-3">
          <View className="gap-1">
            <Text className="text-2xl font-extrabold text-adminDark">
              {advertiser.business_name}
            </Text>
            <Text className="text-xs text-adminMuted">
              Merchant ID: #{advertiser.id} · Onboarded Account
            </Text>
          </View>

          <View className="flex-row items-center gap-2">
            <View
              className="rounded-full px-3 py-1 border"
              style={{
                backgroundColor: APPROVAL_BG[advertiser.approval_status] ?? "rgba(148, 163, 184, 0.12)",
                borderColor: APPROVAL_COLOR[advertiser.approval_status] ?? "#64748b",
              }}
            >
              <Text
                className="text-xs font-bold capitalize"
                style={{ color: APPROVAL_COLOR[advertiser.approval_status] ?? "#64748b" }}
              >
                ● {advertiser.approval_status}
              </Text>
            </View>
          </View>
        </View>

        {/* Overview Stats Cards */}
        <View className="grid grid-cols-2 gap-3 md:flex-row md:gap-4 pt-2 border-t border-adminBorder/60">
          <ProfileStat label="Active Campaigns" value={selectedSummary?.active_campaigns ?? 0} />
          <ProfileStat label="Redemptions" value={selectedSummary?.total_redemptions ?? 0} />
          <ProfileStat label="Total Spend" value={`₹${(selectedSummary?.spend ?? 0).toLocaleString()}`} />
          <ProfileStat label="Contract Expiry" value={advertiser.contract_expiry_date ?? "No Expiry"} />
        </View>
      </View>

      {/* 2. Contact & Store Info Card */}
      <AdminCard heading="👤 Contact & Location Profile">
        <View className="grid gap-3 md:grid-cols-2 pt-1">
          <InfoItem label="Contact Person" value={advertiser.contact_person} icon="👤" />
          <InfoItem label="Email Address" value={advertiser.email || "Not provided"} icon="✉️" />
          <InfoItem label="Phone Number" value={advertiser.phone || "Not provided"} icon="📞" />
          <InfoItem label="Category & Plan" value={`${advertiser.category ?? "Uncategorized"} (${advertiser.plan ?? "No Plan"})`} icon="🏷️" />
          <View className="md:col-span-2">
            <InfoItem label="Store Address" value={advertiser.store_address} icon="📍" />
          </View>
        </View>

        {advertiser.latitude && advertiser.longitude ? (
          <Pressable
            className="mt-2 self-start rounded-lg bg-adminBg px-3 py-1.5 border border-adminBorder"
            onPress={() =>
              Linking.openURL(
                `https://www.google.com/maps/search/?api=1&query=${advertiser.latitude},${advertiser.longitude}`
              )
            }
          >
            <Text className="text-xs font-semibold text-adminPrimary">
              🗺️ Open GPS Coordinates ({advertiser.latitude}, {advertiser.longitude}) →
            </Text>
          </Pressable>
        ) : null}
      </AdminCard>

      {/* 3. Media Upload & Asset Management Section */}
      <AdminCard heading="📷 Media Assets & Upload Management">
        <Text className="text-xs text-adminMuted">
          Upload photo banners and video advertisements specifically assigned to {advertiser.business_name}.
        </Text>

        {/* Upload Form Card */}
        <View className="gap-3 rounded-xl border border-adminBorder bg-adminBg p-4 mt-1">
          <Text className="text-xs font-bold uppercase tracking-wider text-adminDark">
            Upload New Ad Media
          </Text>

          <TextInput
            className="rounded-xl border border-adminBorder bg-adminSurface px-4 py-3 text-sm text-adminText"
            placeholder="Enter media title (e.g., Summer Special Ad Banner)"
            placeholderTextColor="#94a3b8"
            value={mediaTitle}
            onChangeText={setMediaTitle}
          />

          <View className="flex-row gap-3">
            <Pressable
              className="flex-1 rounded-xl border border-adminPrimary bg-adminSurface p-3 shadow-sm"
              onPress={() => {
                onUpload("photo", mediaTitle);
                setMediaTitle("");
              }}
              disabled={isUploading}
            >
              <Text className="text-center font-bold text-adminPrimary">
                📷 Upload Photo Banner
              </Text>
            </Pressable>

            <Pressable
              className="flex-1 rounded-xl bg-adminPrimary p-3 shadow-sm"
              onPress={() => {
                onUpload("video", mediaTitle);
                setMediaTitle("");
              }}
              disabled={isUploading}
            >
              <Text className="text-center font-bold text-white">
                🎬 Upload Video Ad
              </Text>
            </Pressable>
          </View>

          {isUploading ? (
            <Text className="text-center text-xs font-semibold text-adminPrimary">
              Uploading media asset to server...
            </Text>
          ) : null}
        </View>

        {/* Gallery Grid */}
        <View className="gap-3 pt-3">
          <Text className="text-sm font-bold text-adminDark">
            Uploaded Media Assets ({advertiser.media.length})
          </Text>

          {advertiser.media.length === 0 ? (
            <View className="rounded-xl border border-dashed border-adminBorder p-6 items-center">
              <Text className="text-adminMuted text-xs font-medium">
                No photo or video assets uploaded for this advertiser yet.
              </Text>
            </View>
          ) : (
            <View className="grid gap-3 md:grid-cols-2">
              {advertiser.media.map((media) => (
                <MediaCard
                  key={media.id}
                  media={media}
                  onDelete={() => onDeleteMedia(media)}
                />
              ))}
            </View>
          )}
        </View>
      </AdminCard>

      {/* 4. Assigned Rickshaws (Fleet) Section */}
      <AdminCard heading={`🛺 Assigned Rickshaws (${advertiser.rickshaws.length})`}>
        <Text className="text-xs text-adminMuted">
          Rickshaws mapped to display advertisements for this merchant. Uniquely identified by registration number plate.
        </Text>

        {advertiser.rickshaws.length === 0 ? (
          <View className="rounded-xl border border-dashed border-adminBorder p-6 items-center">
            <Text className="text-adminMuted text-xs font-medium">
              No rickshaws currently assigned to this merchant.
            </Text>
          </View>
        ) : (
          <View className="gap-2.5 pt-1">
            {advertiser.rickshaws.map((rickshaw) => (
              <View
                key={rickshaw.id}
                className="flex-row items-center justify-between rounded-xl bg-adminBg p-3.5 border border-adminBorder/70"
              >
                <View className="flex-row items-center gap-3">
                  <View className="rounded-lg bg-yellow-400 px-2.5 py-1 border border-yellow-500 shadow-sm">
                    <Text className="font-extrabold text-xs text-black">
                      {rickshaw.registration_number}
                    </Text>
                  </View>

                  <View>
                    <Text className="font-bold text-sm text-adminDark">
                      Driver: {rickshaw.driver_name ?? "Unassigned"}
                    </Text>
                    <Text className="text-xs text-adminMuted">
                      Hardware Unit: {rickshaw.hardware_serial ? `HW #${rickshaw.hardware_serial}` : "None"}
                    </Text>
                  </View>
                </View>

                <View
                  className="rounded-full px-3 py-1"
                  style={{
                    backgroundColor:
                      rickshaw.status === "active"
                        ? "rgba(34, 197, 94, 0.12)"
                        : "rgba(148, 163, 184, 0.12)",
                  }}
                >
                  <Text
                    className="text-xs font-bold uppercase"
                    style={{
                      color: RICKSHAW_STATUS_COLOR[rickshaw.status] ?? "#94a3b8",
                    }}
                  >
                    {rickshaw.status}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}
      </AdminCard>
    </View>
  );
}

/* ── Single media card component ─────────────────────────────────────── */

function MediaCard({
  media,
  onDelete,
}: {
  media: AdMedia;
  onDelete: () => void;
}) {
  const url = fileUrl(media.file);
  const isVideo = media.media_type === "video";

  return (
    <View className="gap-2.5 rounded-xl border border-adminBorder bg-adminBg p-3.5 shadow-sm">
      {/* Preview */}
      {isVideo ? (
        <View className="h-36 w-full items-center justify-center rounded-lg bg-slate-900 border border-slate-800 shadow-inner">
          <Text className="text-4xl text-white">▶</Text>
          <Text className="pt-1 text-xs font-bold text-slate-300">
            Video Asset · Tap to play
          </Text>
        </View>
      ) : (
        <Image
          source={{ uri: url }}
          className="h-36 w-full rounded-lg border border-adminBorder"
          resizeMode="cover"
        />
      )}

      {/* Info row */}
      <View className="flex-row items-center justify-between pt-1">
        <View className="flex-1 pr-2">
          <Text className="font-bold text-sm text-adminDark">{media.title}</Text>
          <Text className="text-xs text-adminMuted">
            Type: {media.media_type} · Date: {new Date(media.created_at).toLocaleDateString()}
          </Text>
        </View>
      </View>

      {/* Action buttons */}
      <View className="flex-row gap-2 pt-1">
        <Pressable
          className="flex-1 rounded-xl border border-adminBorder bg-adminSurface p-2.5 shadow-sm"
          onPress={() => Linking.openURL(url)}
        >
          <Text className="text-center font-bold text-xs text-adminPrimary">
            {isVideo ? "▶ Play Video" : "🔍 View Full Image"}
          </Text>
        </Pressable>

        <Pressable
          className="rounded-xl bg-red-500 px-4 p-2.5 shadow-sm"
          onPress={onDelete}
        >
          <Text className="text-center font-bold text-xs text-white">Delete</Text>
        </Pressable>
      </View>
    </View>
  );
}

/* ── Small profile metric box ─────────────────────────────────────────── */

function ProfileStat({ label, value }: { label: string; value: number | string }) {
  return (
    <View className="min-w-[120px] flex-1 rounded-xl bg-adminBg p-3 border border-adminBorder/70">
      <Text className="text-[10px] font-bold uppercase tracking-wider text-adminMuted">
        {label}
      </Text>
      <Text className="pt-1 text-base font-extrabold text-adminDark">
        {typeof value === "number" ? value.toLocaleString() : value}
      </Text>
    </View>
  );
}

/* ── Info key-value row ──────────────────────────────────────────────── */

function InfoItem({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <View className="gap-0.5">
      <Text className="text-[10px] font-bold uppercase tracking-wider text-adminMuted">
        {icon} {label}
      </Text>
      <Text className="text-sm font-semibold text-adminDark">{value}</Text>
    </View>
  );
}

/* ── Directory card metric item ──────────────────────────────────────── */

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <View>
      <Text className="text-[10px] font-bold uppercase tracking-wider text-adminMuted">
        {label}
      </Text>
      <Text className="text-sm font-extrabold text-adminDark">{value}</Text>
    </View>
  );
}
