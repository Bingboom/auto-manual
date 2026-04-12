import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

import { createStateStore } from "../lib/state-store.mjs";

test("claimProcessedEvent serializes concurrent duplicate claims", async () => {
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "feishu-im-state-"));
  const stateFile = path.join(tempDir, "state.json");
  const store = createStateStore(stateFile);

  const [first, second] = await Promise.all([
    store.claimProcessedEvent("evt_dup"),
    store.claimProcessedEvent("evt_dup"),
  ]);

  assert.deepEqual([first, second].sort(), [false, true]);
});
