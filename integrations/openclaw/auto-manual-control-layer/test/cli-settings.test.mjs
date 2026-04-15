import test from "node:test";
import assert from "node:assert/strict";

import { parseRepositoryFromRemoteUrl } from "../lib/cli-settings.mjs";

test("parseRepositoryFromRemoteUrl supports https remotes", () => {
  assert.deepEqual(parseRepositoryFromRemoteUrl("https://github.com/example/auto-manual.git"), {
    repoOwner: "example",
    repoName: "auto-manual",
  });
});

test("parseRepositoryFromRemoteUrl supports ssh remotes", () => {
  assert.deepEqual(parseRepositoryFromRemoteUrl("git@github.com:example/auto-manual.git"), {
    repoOwner: "example",
    repoName: "auto-manual",
  });
});

test("parseRepositoryFromRemoteUrl returns null for unsupported input", () => {
  assert.equal(parseRepositoryFromRemoteUrl(""), null);
  assert.equal(parseRepositoryFromRemoteUrl("not-a-remote"), null);
});
