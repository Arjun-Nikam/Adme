import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import type { Role } from "@/lib/roles";

export interface AuthState {
  status: "loading" | "authenticated" | "anonymous";
  role: Role | null;
  name: string | null;
  userId: number | null;
  merchantId: number | null;
  consumerId: number | null;
  driverId: number | null;
}

const initialState: AuthState = {
  status: "loading", // resolved by the root layout bootstrap
  role: null,
  name: null,
  userId: null,
  merchantId: null,
  consumerId: null,
  driverId: null,
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    sessionRestored(
      state,
      action: PayloadAction<{ role: Role | null; name?: string | null }>,
    ) {
      state.status = action.payload.role ? "authenticated" : "anonymous";
      state.role = action.payload.role;
      state.name = action.payload.name ?? null;
    },
    loginSucceeded(
      state,
      action: PayloadAction<{ role: Role; name: string; userId: number }>,
    ) {
      state.status = "authenticated";
      state.role = action.payload.role;
      state.name = action.payload.name;
      state.userId = action.payload.userId;
    },
    profileHydrated(
      state,
      action: PayloadAction<{
        name?: string | null;
        merchantId: number | null;
        consumerId: number | null;
        driverId: number | null;
      }>,
    ) {
      if (action.payload.name) state.name = action.payload.name;
      state.merchantId = action.payload.merchantId;
      state.consumerId = action.payload.consumerId;
      state.driverId = action.payload.driverId;
    },
    loggedOut(state) {
      state.status = "anonymous";
      state.role = null;
      state.name = null;
      state.userId = null;
      state.merchantId = null;
      state.consumerId = null;
      state.driverId = null;
    },
  },
});

export const { sessionRestored, loginSucceeded, profileHydrated, loggedOut } =
  authSlice.actions;
export default authSlice.reducer;
