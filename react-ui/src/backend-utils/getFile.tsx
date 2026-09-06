import fs from "fs";
import path from "path";

// Files referenced by API callers are always relative to public/, which is the
// directory the upload route writes into. `path.join` resolves "..", so the
// joined result must be re-checked against the root before it is read.
const PUBLIC_ROOT = path.resolve(process.cwd(), "public");

export const getFile = (file: string) =>
  file
    ? file.startsWith("http") || file.startsWith("data")
      ? readFromURL(file)
      : readFromDisk(file)
    : null;

const readFromDisk = (file: string) =>
  new Promise((resolve, reject) => {
    const target = path.resolve(PUBLIC_ROOT, "." + path.sep + file);

    if (target !== PUBLIC_ROOT && !target.startsWith(PUBLIC_ROOT + path.sep)) {
      reject(new Error("Refusing to read outside the public directory"));
      return;
    }

    fs.readFile(target, (err, data) => {
      if (err) reject(err);
      resolve(data);
    });
  });

// Only plain http(s) is fetched, and only when the caller opted into a remote
// URL. data: URLs are handled by fetch itself and stay local to the process.
const readFromURL = (file: string) => {
  if (file.startsWith("data:")) return fetch(file).then((r) => r.blob());

  let parsed: URL;
  try {
    parsed = new URL(file);
  } catch {
    return Promise.reject(new Error("Invalid URL"));
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    return Promise.reject(new Error("Unsupported URL scheme"));
  }

  if (isBlockedHost(parsed.hostname)) {
    return Promise.reject(new Error("Refusing to fetch internal address"));
  }

  return fetch(parsed.toString()).then((r) => r.blob());
};

// Block the obvious SSRF targets: loopback, link-local (cloud metadata) and
// the RFC1918 ranges. Hostnames that resolve to these are still possible via
// DNS, so treat this as a speed bump rather than a boundary.
const isBlockedHost = (hostname: string) => {
  const host = hostname.replace(/^\[|\]$/g, "").toLowerCase();

  if (host === "localhost" || host.endsWith(".localhost")) return true;
  if (host === "::1" || host === "0.0.0.0") return true;
  if (host === "metadata.google.internal") return true;

  const v4 = host.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (!v4) return false;

  const [a, b] = v4.slice(1).map(Number);
  if (a === 127 || a === 10 || a === 0) return true;
  if (a === 169 && b === 254) return true;
  if (a === 192 && b === 168) return true;
  if (a === 172 && b >= 16 && b <= 31) return true;

  return false;
};
