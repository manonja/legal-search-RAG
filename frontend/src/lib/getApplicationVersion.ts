import fs from "fs";
import path from "path";

/**
 * Gets the application version from either package.json or VERSION file
 * @returns The version string or null if not found
 */
export function getApplicationVersion(): string | null {
  try {
    // First try to read from VERSION file (used by Docker builds)
    const versionPath = path.join(process.cwd(), "VERSION");
    if (fs.existsSync(versionPath)) {
      const version = fs.readFileSync(versionPath, "utf8").trim();
      if (version) return version;
    }

    // Fall back to package.json
    const packagePath = path.join(process.cwd(), "package.json");
    if (fs.existsSync(packagePath)) {
      const packageJson = JSON.parse(fs.readFileSync(packagePath, "utf8"));
      if (packageJson.version) return packageJson.version;
    }

    // If we got here, we couldn't find a version
    console.warn("Could not determine application version");
    return null;
  } catch (error) {
    console.error("Error getting application version:", error);
    return null;
  }
}
