import type { NextApiRequest, NextApiResponse } from "next";
import { defaultBackend } from "../../../backend-utils/defaultBackend";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    // Get the path from the URL
    const { path } = req.query;
    
    if (!path || !Array.isArray(path) || path.length === 0) {
      return res.status(400).json({ error: "Invalid path" });
    }

    // Reconstruct the original path
    const originalPath = path.join("/");
    
    // Construct the full URL to the Gradio backend
    let gradioUrl: string;
    
    // handle auth
    // const auth = process.env.GRADIO_AUTH;
    // if (auth) {
    //   const [username, password] = auth.split(":");
    //   const authHeader = `Basic ${Buffer.from(`${username}:${password}`).toString('base64')}`;
    //   req.headers.authorization = authHeader;
    // }

    // Handle the special case for gradio_api/file= format
    if (originalPath.startsWith("gradio_api/file=")) {
      // For URLs like: gradio_api/file=C:/Users/rob/AppData/Local/Temp/gradio/...
      const filePath = originalPath.substring("gradio_api/file=".length);
      gradioUrl = `${defaultBackend}gradio_api/file=${filePath}`;
    } else {
      // For regular file URLs
      gradioUrl = `${defaultBackend}${originalPath}`;
    }

    // Fetch the file from the Gradio backend
    const response = await fetch(gradioUrl);
    
    if (!response.ok) {
      return res.status(response.status).json({ 
        error: `Failed to fetch file from Gradio backend: ${response.statusText}` 
      });
    }

    // Get content type and other headers from the response
    const contentType = response.headers.get("content-type");
    const contentLength = response.headers.get("content-length");
    const contentDisposition = response.headers.get("content-disposition");

    // Do not reflect the upstream Content-Type. This response is served from
    // the UI's own origin, so an .html file reachable through Gradio's
    // allowed_paths would otherwise execute as same-origin script.
    const baseType = (contentType ?? "").split(";")[0].trim().toLowerCase();
    const isRenderable =
      /^(audio|image|video)\//.test(baseType) ||
      baseType === "application/json" ||
      baseType === "text/plain";

    res.setHeader(
      "Content-Type",
      isRenderable ? (contentType as string) : "application/octet-stream"
    );
    res.setHeader("X-Content-Type-Options", "nosniff");
    if (contentLength) {
      res.setHeader("Content-Length", contentLength);
    }
    if (contentDisposition) {
      res.setHeader("Content-Disposition", contentDisposition);
    }
    
    // Stream the response body
    const body = await response.arrayBuffer();
    res.send(Buffer.from(body));
  } catch (error) {
    console.error("Error proxying Gradio file:", error);
    res.status(500).json({ error: "Failed to proxy file" });
  }
}

// Configure API to handle large files
export const config = {
  api: {
    responseLimit: false,
    bodyParser: false,
  },
};
