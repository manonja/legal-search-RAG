/**
 * Gets system diagnostics for non-production environments
 * @returns Object containing diagnostic information
 */
export function getSystemDiagnostics() {
  const startTime = process.uptime();
  const uptime = formatUptime(startTime);

  return {
    memoryUsage: formatMemoryUsage(process.memoryUsage().heapUsed),
    uptime,
    nodeVersion: process.version,
  };
}

/**
 * Formats memory usage in a human-readable format
 * @param bytes Memory usage in bytes
 * @returns Formatted memory usage string
 */
function formatMemoryUsage(bytes: number): string {
  const mb = bytes / 1024 / 1024;
  return `${Math.round(mb * 100) / 100}MB`;
}

/**
 * Formats uptime in a human-readable format
 * @param seconds Uptime in seconds
 * @returns Formatted uptime string (e.g., "3d 4h 12m")
 */
function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / (3600 * 24));
  const hours = Math.floor((seconds % (3600 * 24)) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  let result = "";
  if (days > 0) result += `${days}d `;
  if (hours > 0 || days > 0) result += `${hours}h `;
  result += `${minutes}m`;

  return result;
}
