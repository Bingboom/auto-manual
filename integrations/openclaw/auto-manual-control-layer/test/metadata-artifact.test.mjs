import test from "node:test";
import assert from "node:assert/strict";

import AdmZip from "adm-zip";

import { extractMetadataFromZipBuffer } from "../lib/metadata-artifact.mjs";

test("extractMetadataFromZipBuffer reads the first json payload", () => {
  const zip = new AdmZip();
  zip.addFile("openclaw-run.json", Buffer.from(JSON.stringify({ queue_record_id: "rec123", publish_url: "https://publish.example.com" })));

  const payload = extractMetadataFromZipBuffer(zip.toBuffer());

  assert.equal(payload.queue_record_id, "rec123");
  assert.equal(payload.publish_url, "https://publish.example.com");
});
