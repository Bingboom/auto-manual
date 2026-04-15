import AdmZip from "adm-zip";

export function extractMetadataFromZipBuffer(buffer) {
  const zip = new AdmZip(buffer);
  const entry = zip
    .getEntries()
    .find((candidate) => !candidate.isDirectory && candidate.entryName.toLowerCase().endsWith(".json"));
  if (!entry) {
    return null;
  }
  return JSON.parse(entry.getData().toString("utf8"));
}
