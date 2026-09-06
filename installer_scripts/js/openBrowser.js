const { execFile } = require("child_process");

// Function to open the browser
function openBrowser(url) {
  // Only ever open plain http(s). Guards against a future caller passing
  // something else through to the platform opener.
  let parsed;
  try {
    parsed = new URL(url);
  } catch (error) {
    console.error(`Refusing to open invalid URL: ${url}`);
    return;
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    console.error(`Refusing to open non-http URL: ${url}`);
    return;
  }

  // Determine the command based on the platform. Arguments are passed as a
  // list rather than interpolated into a shell string.
  let command;
  let args;
  switch (process.platform) {
    case "win32":
      command = "cmd";
      args = ["/c", "start", "", parsed.toString()];
      break;
    case "darwin":
      command = "open";
      args = ["--", parsed.toString()];
      break;
    default:
      command = "xdg-open";
      args = [parsed.toString()];
      break;
  }

  execFile(command, args, (error) => {
    if (error) {
      console.error(`Failed to open browser: ${error.message}`);
    }
  });
}
exports.openBrowser = openBrowser;
