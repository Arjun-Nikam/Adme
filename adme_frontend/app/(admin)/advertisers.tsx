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

  return (
    <AdminScreen subtitle="Advertisers">
      {/* Filter Tabs */}
      <View className="flex-row flex-wrap gap-2 pb-2">
        {(["approved", "pending", "rejected", "all"] as const).map((tab) => {
          const isActive = statusFilter === tab;
          return (
            <Pressable
              key={tab}
              onPress={() => setStatusFilter(tab)}
              className={`rounded-full px-4 py-1.5 border ${
                isActive
                  ? "bg-adminPrimary border-adminPrimary"
                  : "bg-adminSurface border-adminBorder"
              }`}
            >
              <Text
                className={`text-xs font-semibold capitalize ${
                  isActive ? "text-white" : "text-adminMuted"
                }`}
              >
                {tab}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {isLoading ? (
        <AdminCard>
          <Text className="text-adminMuted">Loading directory...</Text>
        </AdminCard>
      ) : null}

      {isError ? (
        <AdminCard heading="Couldn't load">
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

      {filteredData.map((advertiser) => (
        <View
          key={advertiser.id}
          className="gap-2 rounded-2xl border border-adminBorder bg-adminSurface p-5"
        >
          <Pressable
            onPress={() =>
              setSelectedId(selectedId === advertiser.id ? null : advertiser.id)
            }
          >
            <View className="flex-row items-center justify-between">
              <Text className="text-base font-bold text-adminDark">
                {advertiser.business_name}
              </Text>
              <Text className="font-semibold text-adminPrimary">
                {selectedId === advertiser.id ? "Hide details" : "View details"}
              </Text>
            </View>

            <View className="flex-row items-center gap-3 pt-2">
              <View
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: 4,
                  backgroundColor:
                    STATUS_COLOR[advertiser.renewal_status] ?? "#64748b",
                }}
              />
              <Text className="text-xs font-semibold text-adminMuted">
                {advertiser.renewal_status}
              </Text>
              <Text
                className="text-xs font-semibold"
                style={{
                  color: APPROVAL_COLOR[advertiser.approval_status],
                }}
              >
                {advertiser.approval_status}
              </Text>
            </View>

            <Text className="pt-2 text-xs text-adminMuted">
              {advertiser.category ?? "—"} · {advertiser.plan ?? "no plan"}
              {advertiser.contract_expiry_date
                ? ` · expires ${advertiser.contract_expiry_date}`
                : ""}
            </Text>

            <View className="flex-row gap-4 pt-3">
              <Metric label="Live campaigns" value={advertiser.active_campaigns} />
              <Metric label="Redemptions" value={advertiser.total_redemptions} />
              <Metric
                label="Spend"
                value={`₹${advertiser.spend.toLocaleString()}`}
              />
            </View>
          </Pressable>

          {selectedId === advertiser.id ? (
            <AdvertiserDetails
              detail={detail}
              isUploading={isUploading}
              onUpload={uploadMedia}
              onDeleteMedia={handleDeleteMedia}
            />
          ) : null}
        </View>
      ))}

      {data && data.length === 0 ? (
        <AdminCard>
          <Text className="text-adminMuted">No advertisers onboarded yet.</Text>
        </AdminCard>
      ) : null}
    </AdminScreen>
  );
}

/* ── Advertiser expanded detail panel ────────────────────────────────── */

function AdvertiserDetails({
  detail,
  isUploading,
  onUpload,
  onDeleteMedia,
}: {
  detail: { isLoading: boolean; isError?: boolean; data?: AdvertiserDetail };
  isUploading: boolean;
  onUpload: (type: "photo" | "video", title: string) => void;
  onDeleteMedia: (media: AdMedia) => void;
}) {
  const [mediaTitle, setMediaTitle] = useState("");

  if (detail.isLoading || !detail.data) {
    return (
      <Text className="pt-3 text-adminMuted">
        Loading advertiser details...
      </Text>
    );
  }

  if (detail.isError) {
    return (
      <Text className="pt-3 text-red-500">
        Failed to load advertiser details. Please try again.
      </Text>
    );
  }

  const advertiser = detail.data;

  return (
    <View className="mt-3 gap-4 border-t border-adminBorder pt-4">
      {/* ── Contact & Location ─────────────────────────────────── */}
      <View className="gap-1">
        <Text className="font-bold text-adminDark">Contact and location</Text>
        <Text className="text-adminMuted">
          {advertiser.contact_person} ·{" "}
          {advertiser.email || advertiser.phone}
        </Text>
        <Text className="text-adminMuted">{advertiser.store_address}</Text>
        <Text className="text-xs text-adminMuted">
          GPS: {advertiser.latitude}, {advertiser.longitude}
        </Text>
      </View>

      {/* ── Media Upload & Gallery ─────────────────────────────── */}
      <View className="gap-2">
        <Text className="font-bold text-adminDark">Advertiser media</Text>

        {/* Title input */}
        <TextInput
          className="rounded-xl border border-adminBorder bg-adminBg px-4 py-3 text-adminText"
          placeholder="Media title (optional)"
          placeholderTextColor="#94a3b8"
          value={mediaTitle}
          onChangeText={setMediaTitle}
        />

        {/* Upload buttons */}
        <View className="flex-row gap-2">
          <Pressable
            className="flex-1 rounded-xl border border-adminBorder p-3"
            onPress={() => {
              onUpload("photo", mediaTitle);
              setMediaTitle("");
            }}
            disabled={isUploading}
          >
            <Text className="text-center font-semibold text-adminPrimary">
              📷 Upload photo
            </Text>
          </Pressable>
          <Pressable
            className="flex-1 rounded-xl bg-primary p-3"
            onPress={() => {
              onUpload("video", mediaTitle);
              setMediaTitle("");
            }}
            disabled={isUploading}
          >
            <Text className="text-center font-semibold text-white">
              🎬 Upload video
            </Text>
          </Pressable>
        </View>

        {isUploading ? (
          <Text className="text-adminMuted">Uploading...</Text>
        ) : null}

        {/* Media items gallery */}
        {advertiser.media.map((media) => (
          <MediaCard
            key={media.id}
            media={media}
            onDelete={() => onDeleteMedia(media)}
          />
        ))}

        {advertiser.media.length === 0 ? (
          <Text className="text-adminMuted">
            No media uploaded for this advertiser.
          </Text>
        ) : null}
      </View>

      {/* ── Assigned Rickshaws ─────────────────────────────────── */}
      <View className="gap-2">
        <Text className="font-bold text-adminDark">
          Assigned rickshaws ({advertiser.rickshaws.length})
        </Text>

        {advertiser.rickshaws.map((rickshaw) => (
          <View
            key={rickshaw.id}
            className="flex-row items-center justify-between rounded-xl bg-adminBg p-3"
          >
            <View className="flex-row items-center gap-3">
              <View
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: 5,
                  backgroundColor:
                    RICKSHAW_STATUS_COLOR[rickshaw.status] ?? "#94a3b8",
                }}
              />
              <View>
                <Text className="font-bold text-adminDark">
                  {rickshaw.registration_number}
                </Text>
                <Text className="text-xs text-adminMuted">
                  {rickshaw.driver_name ?? "No driver assigned"}
                  {rickshaw.hardware_serial
                    ? ` · HW: ${rickshaw.hardware_serial}`
                    : ""}
                </Text>
              </View>
            </View>
            <View
              className="rounded-lg px-2 py-1"
              style={{
                backgroundColor:
                  rickshaw.status === "active"
                    ? "rgba(34, 197, 94, 0.1)"
                    : "rgba(148, 163, 184, 0.1)",
              }}
            >
              <Text
                className="text-xs font-semibold"
                style={{
                  color:
                    RICKSHAW_STATUS_COLOR[rickshaw.status] ?? "#94a3b8",
                }}
              >
                {rickshaw.status}
              </Text>
            </View>
          </View>
        ))}

        {advertiser.rickshaws.length === 0 ? (
          <Text className="text-adminMuted">No rickshaws assigned.</Text>
        ) : null}
      </View>
    </View>
  );
}

/* ── Single media card ───────────────────────────────────────────────── */

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
    <View className="gap-2 rounded-xl bg-adminBg p-3">
      {/* Preview */}
      {isVideo ? (
        <View className="h-32 w-full items-center justify-center rounded-lg bg-gray-800">
          <Text className="text-3xl">▶</Text>
          <Text className="pt-1 text-xs font-semibold text-gray-300">
            Video · tap to play
          </Text>
        </View>
      ) : (
        <Image
          source={{ uri: url }}
          className="h-32 w-full rounded-lg"
          resizeMode="cover"
        />
      )}

      {/* Info row */}
      <View className="flex-row items-center justify-between">
        <View className="flex-1">
          <Text className="font-semibold text-adminDark">{media.title}</Text>
          <Text className="text-xs text-adminMuted">
            {media.media_type} · {new Date(media.created_at).toLocaleDateString()}
          </Text>
        </View>
      </View>

      {/* Action buttons */}
      <View className="flex-row gap-2">
        <Pressable
          className="flex-1 rounded-xl border border-adminBorder bg-adminSurface p-3"
          onPress={() => Linking.openURL(url)}
        >
          <Text className="text-center font-semibold text-adminPrimary">
            {isVideo ? "▶ Play video" : "🔍 View full"}
          </Text>
        </Pressable>
        <Pressable
          className="rounded-xl bg-red-500 px-4 p-3"
          onPress={onDelete}
        >
          <Text className="text-center font-semibold text-white">Delete</Text>
        </Pressable>
      </View>
    </View>
  );
}

/* ── Small metric label ──────────────────────────────────────────────── */

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <View>
      <Text className="text-[10px] font-semibold uppercase text-adminMuted">
        {label}
      </Text>
      <Text className="text-sm font-bold text-adminText">{value}</Text>
    </View>
  );
}
