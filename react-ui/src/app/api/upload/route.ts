import { writeFile } from "fs/promises";
import path from "path";
import { NextRequest, NextResponse } from "next/server";

const CACHE_DIR = path.resolve(process.cwd(), "public", "file-input-cache");

const MAX_BYTES = 256 * 1024 * 1024;

const ALLOWED_EXTENSIONS = new Set([
  ".wav",
  ".mp3",
  ".ogg",
  ".flac",
  ".m4a",
  ".opus",
  ".webm",
  ".npz",
  ".npy",
  ".png",
  ".jpg",
  ".jpeg",
]);

export async function POST(request: NextRequest) {
  const data = await request.formData();
  const file: File | null = data.get("file") as unknown as File;

  if (!file) {
    return NextResponse.json({ success: false }, { status: 400 });
  }

  // The multipart filename is fully attacker-controlled, so it is never used
  // to build a path. Keep only the final component and drop leading dots.
  const safeName = path.basename(file.name).replace(/^\.+/, "");
  const extension = path.extname(safeName).toLowerCase();

  if (!safeName || !ALLOWED_EXTENSIONS.has(extension)) {
    return NextResponse.json(
      { success: false, error: "Unsupported file type" },
      { status: 400 }
    );
  }

  if (file.size > MAX_BYTES) {
    return NextResponse.json(
      { success: false, error: "File too large" },
      { status: 413 }
    );
  }

  const target = path.resolve(CACHE_DIR, safeName);

  // Defence in depth: refuse anything that resolved outside the cache directory.
  if (!target.startsWith(CACHE_DIR + path.sep)) {
    return NextResponse.json({ success: false }, { status: 400 });
  }

  const bytes = await file.arrayBuffer();
  await writeFile(target, Buffer.from(bytes));

  return NextResponse.json({ success: true, name: safeName });
}
