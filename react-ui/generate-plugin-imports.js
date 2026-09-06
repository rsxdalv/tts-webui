const fs = require("fs");

const getPackageJSON = () => {
  try {
    return require("./src/extensions/package.json").dependencies;
  } catch (error) {
    return {};
  }
};

const main = async () => {
  const installedPackages = getPackageJSON();

  if (!installedPackages || Object.keys(installedPackages).length === 0) {
    console.log("No React UI extensions found");

    fs.writeFileSync(
      "./src/extensions/link.ts",
      `const linkExtension = {};
export default linkExtension;
`
    );
    return;
  }

  // This writes a TypeScript source file that is then bundled and executed, so
  // the package names are validated rather than interpolated blind. A name
  // containing a quote would otherwise close the module specifier and append
  // arbitrary statements. src/extensions/package.json is gitignored and written
  // at install time, so its contents are not necessarily trustworthy.
  const VALID_PACKAGE = /^@tts-webui\/[a-z0-9][a-z0-9._-]*$/;

  const ttsWebuiPackages = Object.keys(installedPackages).filter((x) => {
    if (!x.startsWith("@tts-webui")) return false;
    if (!VALID_PACKAGE.test(x)) {
      console.warn(`Skipping React UI extension with unsafe name: ${x}`);
      return false;
    }
    return true;
  });

  console.log("Found React UI extensions:", ttsWebuiPackages.join(", "));

  const imports = ttsWebuiPackages
    .map((x) => {
      const identifier = x.replace("@tts-webui/", "").replace(/[.-]/g, "_");
      return `export { default as ${identifier} } from ${JSON.stringify(x)};`;
    })
    .join("\n");

  fs.writeFileSync("./src/extensions/link.ts", imports);

  console.log("Generated React UI extensions imports");

  return;
};

main();
