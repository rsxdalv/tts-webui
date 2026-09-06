import { ChangeEvent } from "react";

export const getLocalFileURL = (file?: File) =>
  file && "/file-input-cache/" + file.name;

export const getFilenameFromLocalFileURL = (url?: string) =>
  url?.replace("/file-input-cache/", "");

export const uploadFile = async (file?: File) => {
  if (!file) return;

  try {
    const data = new FormData();
    data.set("file", file);

    const res = await fetch("/api/upload", {
      method: "POST",
      body: data,
      headers: { "x-requested-with": "tts-webui" },
    });
    // handle the error
    if (!res.ok) throw new Error(await res.text());
    // The server sanitises the filename, so use the name it actually wrote.
    const { name } = await res.json();
    return "/file-input-cache/" + name;
  } catch (e: any) {
    // Handle errors here
    console.error(e);
  }
};

const parseFileEvent = (e: ChangeEvent<HTMLInputElement>) =>
  e.target.files?.[0];

export default function FileInput({
  callback,
  accept = "audio/*",
  hide_text = true,
}: {
  callback: (file?: string) => void;
  accept?: string;
  hide_text?: boolean;
}) {
  return (
    <div>
      <input
        type="file"
        name="file"
        onChange={async (e) => {
          const file = parseFileEvent(e);
          const url = await uploadFile(file);
          callback(url);
        }}
        accept={accept}
        style={{
          color: hide_text ? "transparent" : undefined,
        }}
      />
      <button onClick={() => callback(undefined)}>Clear File</button>
    </div>
  );
}
