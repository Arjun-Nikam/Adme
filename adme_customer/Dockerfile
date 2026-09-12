# Dev-only image: runs the Expo web (Metro) dev server for a quick containerised
# preview of the web Ops Screen. iOS/Android work is done on the host with
# `npx expo start` (simulators aren't reachable from the container).
FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 8081
ENV EXPO_NO_TELEMETRY=1 CI=1
CMD ["npx", "expo", "start", "--web", "--port", "8081"]
