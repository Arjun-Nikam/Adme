export type Role =
  | "merchant"
  | "consumer"
  | "admin"
  | "driver"
  | "hardware"
  | "super_admin";

/** Story CORE-1 — where each role lands after login / when hitting a route
 *  it isn't allowed on. Mirrors the backend permission matrix. */
export function roleHome(role: Role | null | undefined): string {
  switch (role) {
    case "merchant":
      return "/(merchant)";
    case "consumer":
      return "/(consumer)";
    case "admin":
      return "/(admin)";
    case "driver":
    case "hardware":
      return "/(rickshaw)";
    case "super_admin":
      return "/(superadmin)";
    default:
      return "/login";
  }
}

/** Decode the `role` claim from a JWT without verifying the signature
 *  (the server verifies; the client only needs to route). */
export function roleFromJwt(token: string): Role | null {
  try {
    const payload = token.split(".")[1];
    const json = JSON.parse(
      decodeURIComponent(
        atob(payload.replace(/-/g, "+").replace(/_/g, "/"))
          .split("")
          .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
          .join(""),
      ),
    );
    return (json.role as Role) ?? null;
  } catch {
    return null;
  }
}
