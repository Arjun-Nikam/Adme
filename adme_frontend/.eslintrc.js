module.exports = {
  root: true,
  extends: ["expo"],
  ignorePatterns: ["/dist", "/.expo", "/node_modules"],
  rules: {},
  overrides: [
    {
      files: ["*.config.js", "babel.config.js", "metro.config.js"],
      env: { node: true },
    },
  ],
};
