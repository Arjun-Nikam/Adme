// Default Expo Metro config. Kept explicit so the frontend Dockerfile / CI can
// rely on it and so future custom resolvers have a home.
const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

const config = getDefaultConfig(__dirname);

module.exports = withNativeWind(config, { input: "./global.css" });
