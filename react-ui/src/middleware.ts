import { NextRequest, NextResponse } from "next/server";

/**
 * Same-origin enforcement for the local API routes.
 *
 * Every route under /api/ performs privileged local work: proxying Gradio
 * calls, reading files off disk, writing uploads. None of them are meant to be
 * reachable from another website, but several accept CORS-safelisted content
 * types ("text/plain", "multipart/form-data"), which browsers send as simple
 * requests with no preflight. Without an Origin check, any page the user
 * visits can drive them.
 *
 * Browsers attach `Origin` to every cross-origin request and to same-origin
 * requests with an unsafe method, so comparing it against the request Host
 * blocks drive-by CSRF without breaking the app or non-browser clients.
 *
 * Set ALLOWED_ORIGINS (comma-separated) to permit additional origins, e.g.
 * when the UI is served from a different host than the API.
 */

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

const extraAllowedOrigins = () =>
  (process.env.ALLOWED_ORIGINS ?? "")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);

const isAllowedOrigin = (origin: string | null, request: NextRequest) => {
  // Non-browser clients (curl, the Gradio SDK, tests) send no Origin.
  if (!origin) return true;

  try {
    const parsed = new URL(origin);
    if (parsed.host === request.headers.get("host")) return true;
    return extraAllowedOrigins().includes(parsed.origin);
  } catch {
    return false;
  }
};

export function middleware(request: NextRequest) {
  if (SAFE_METHODS.has(request.method)) return NextResponse.next();

  // Sec-Fetch-Site is unforgeable by page script where it is supported.
  const site = request.headers.get("sec-fetch-site");
  if (site && site !== "same-origin" && site !== "none") {
    return NextResponse.json(
      { error: "Cross-origin request rejected" },
      { status: 403 }
    );
  }

  if (!isAllowedOrigin(request.headers.get("origin"), request)) {
    return NextResponse.json(
      { error: "Cross-origin request rejected" },
      { status: 403 }
    );
  }

  return NextResponse.next();
}

export const config = {
  matcher: "/api/:path*",
};
