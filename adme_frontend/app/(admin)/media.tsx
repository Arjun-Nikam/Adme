import { useState } from "react";
import { Alert, Image, Linking, Pressable, Text, TextInput, View } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { AdminCard, AdminScreen } from "@/components/AdminScreen";
import {
  useAdMediaQuery,
  useDeleteAdMediaMutation,
  useUploadAdMediaMutation,
} from "@/api/adminApi";
import { baseURL } from "@/api/httpClient";

function fileUrl(file: string) {
  return file.startsWith("http") ? file : `${baseURL.replace(/\/api\/v1\/?$/, "")}${file.startsWith("/") ? "" : "/"}${file}`;
}

export default function MediaLibrary() {
  const { data, isLoading, isError, refetch } = useAdMediaQuery();
  const [upload, { isLoading: isUploading }] = useUploadAdMediaMutation();
  const [remove] = useDeleteAdMediaMutation();
  const [title, setTitle] = useState("");

  async function chooseMedia(mediaType: "photo" | "video") {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: mediaType === "photo" ? ["images"] : ["videos"],
      quality: 1,
    });
    if (result.canceled || !result.assets[0]) return;

    const asset = result.assets[0];
    const response = await fetch(asset.uri);
    const blob = await response.blob();
    const formData = new FormData();
    formData.append("title", title.trim() || asset.fileName || `${mediaType} upload`);
    formData.append("media_type", mediaType);
    formData.append("file", blob, asset.fileName || `${mediaType}-${Date.now()}`);

    try {
      await upload(formData).unwrap();
      setTitle("");
    } catch {
      Alert.alert("Upload failed", "The media file could not be uploaded.");
    }
  }

  async function deleteMedia(id: number) {
    Alert.alert(
      "Delete media",
      "Are you sure you want to delete this media? This cannot be undone.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await remove(id).unwrap();
            } catch {
              Alert.alert("Delete failed", "The media file could not be deleted.");
            }
          },
        },
      ],
    );
  }

  return (
    <AdminScreen subtitle="Media library" readOnly={false}>
      <AdminCard heading="Upload media">
        <Text className="text-adminMuted">Choose a photo or video from this device.</Text>
        <TextInput
          className="mt-2 rounded-xl border border-adminBorder bg-adminBg px-4 py-3 text-adminText"
          placeholder="Media title (optional)"
          placeholderTextColor="#94a3b8"
          value={title}
          onChangeText={setTitle}
        />
        <View className="gap-2 pt-2">
          <Pressable className="rounded-xl border border-adminBorder bg-adminSurface p-3" onPress={() => chooseMedia("photo")} disabled={isUploading}>
            <Text className="text-center font-semibold text-adminPrimary">📷 Choose photo</Text>
          </Pressable>
          <Pressable className="rounded-xl bg-primary p-3" onPress={() => chooseMedia("video")} disabled={isUploading}>
            <Text className="text-center font-semibold text-white">🎬 Choose video</Text>
          </Pressable>
        </View>
        {isUploading ? <Text className="pt-2 text-adminMuted">Uploading...</Text> : null}
      </AdminCard>


      {isLoading ? <Text className="text-adminMuted">Loading saved media...</Text> : null}
      {isError ? (
        <AdminCard heading="Could not load media">
          <Text className="text-adminMuted" onPress={() => refetch()}>Tap to retry.</Text>
        </AdminCard>
      ) : null}
      {(data ?? []).map((media) => {
        const url = fileUrl(media.file);
        const isVideo = media.media_type === "video";
        return (
          <AdminCard key={media.id} heading={media.title}>
            {isVideo ? (
              <View className="h-40 w-full items-center justify-center rounded-lg bg-gray-800">
                <Text className="text-3xl">▶</Text>
                <Text className="pt-1 text-xs font-semibold text-gray-300">
                  Video · tap Open to play
                </Text>
              </View>
            ) : (
              <Image source={{ uri: url }} className="h-40 w-full rounded-lg" resizeMode="cover" />
            )}
            <Text className="text-adminMuted">
              {media.media_type} · {new Date(media.created_at).toLocaleDateString()}
              {media.merchant_name ? ` · ${media.merchant_name}` : ""}
            </Text>
            <View className="flex-row gap-2 pt-2">
              <Pressable className="flex-1 rounded-xl border border-adminBorder bg-adminSurface p-3" onPress={() => Linking.openURL(url)}>
                <Text className="text-center font-semibold text-adminPrimary">
                  {isVideo ? "▶ Play" : "🔍 Open"}
                </Text>
              </Pressable>
              <Pressable className="rounded-xl bg-red-500 px-4 p-3" onPress={() => deleteMedia(media.id)}>
                <Text className="text-center font-semibold text-white">Delete</Text>
              </Pressable>
            </View>
          </AdminCard>
        );
      })}
      {!isLoading && !isError && data?.length === 0 ? (
        <AdminCard><Text className="text-adminMuted">No saved photos or videos yet.</Text></AdminCard>
      ) : null}
    </AdminScreen>
  );
}
