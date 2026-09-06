// pages/api/webui-generations/[...name].ts

// Tell Next.js to pass in Node.js HTTP
export const config = {
  api: { externalResolver: true },
};

import express from "express";
import path from "path";
import { webuiBasePath } from "../../../data/getVoicesData";

const handler = express();

const simpleLogger = (req, res, next) => {
  console.log(req.method, req.url);
  next();
};

handler.use(simpleLogger);

// Only generation output directories are served.
//
// This previously mounted express.static() on `webuiBasePath`, which is the
// TTS WebUI project root, exposing config.json, env_store.json, the SQLite
// database under data/, installer logs and the entire source tree over HTTP
// with no authentication.
const SERVED_DIRECTORIES = [
  "outputs",
  "favorites",
  "voices",
  "collections",
  "outputs-rvc",
  "voices-tortoise",
];

for (const directory of SERVED_DIRECTORIES) {
  handler.use(
    `/api/webui-generations/${directory}`,
    express.static(path.join(webuiBasePath, directory), {
      dotfiles: "deny",
      index: false,
      redirect: false,
    })
  );
}

handler.use(["/api/webui-generations"], (_req, res) => {
  res.status(404).end();
});

// express is just a function that takes (http.IncomingMessage, http.ServerResponse),
// which Next.js supports when externalResolver is enabled.
export default handler;
