import test from "node:test";
import assert from "node:assert/strict";

import { extractMetadataFromArtifactBuffer } from "../lib/github-client.mjs";

test("extractMetadataFromArtifactBuffer returns parsed metadata when extractor loads", async () => {
  const payload = await extractMetadataFromArtifactBuffer(Buffer.from("ignored"), {
    loadExtractor: async () => ({
      extractMetadataFromZipBuffer() {
        return { queue_record_id: "rec123", publish_url: "https://publish.example.com" };
      },
    }),
  });

  assert.deepEqual(payload, {
    queue_record_id: "rec123",
    publish_url: "https://publish.example.com",
  });
});

test("extractMetadataFromArtifactBuffer treats missing adm-zip as optional", async () => {
  const payload = await extractMetadataFromArtifactBuffer(Buffer.from("ignored"), {
    loadExtractor: async () => {
      const error = new Error("Cannot find package 'adm-zip' imported from metadata-artifact.mjs");
      error.code = "ERR_MODULE_NOT_FOUND";
      throw error;
    },
  });

  assert.equal(payload, null);
});

test("extractMetadataFromArtifactBuffer rethrows unrelated loader failures", async () => {
  await assert.rejects(
    () =>
      extractMetadataFromArtifactBuffer(Buffer.from("ignored"), {
        loadExtractor: async () => {
          throw new Error("bad zip");
        },
      }),
    /bad zip/
  );
});
