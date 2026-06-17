import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

import {
  applyLocalAliases,
  emptyLocalProfile,
  loadLocalProfile,
  localReactionEmojiType,
  localReplyPhrase,
  normalizeFeishuEmojiType,
} from "../lib/local-profile.mjs";

async function withTempDir(callback) {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "openclaw-local-profile-"));
  try {
    return await callback(dir);
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
}

test("loadLocalProfile treats missing local files as an empty profile", async () => {
  await withTempDir(async (dir) => {
    const profile = loadLocalProfile(dir);

    assert.deepEqual(profile.aliases, []);
    assert.deepEqual(profile.replyPhrases, {});
    assert.deepEqual(profile.reactions, {});
    assert.equal(profile.personaText, "");
    assert.deepEqual(profile.loadedFiles, []);
  });
});

test("loadLocalProfile reads local-only aliases, reply phrases, and reactions", async () => {
  await withTempDir(async (dir) => {
    await fs.writeFile(
      path.join(dir, "aliases.local.json"),
      JSON.stringify({
        aliases: [
          { from: ["private short phrase", "another short phrase"], to: "JE-1000F US" },
          { from: "draft done?", to: "build draft package status" },
        ],
      }),
      "utf8"
    );
    await fs.writeFile(
      path.join(dir, "reply-phrases.local.json"),
      JSON.stringify({
        completionPrefix: "Done:",
        ignoredKey: "not loaded",
      }),
      "utf8"
    );
    await fs.writeFile(
      path.join(dir, "reactions.local.json"),
      JSON.stringify({
        received: "🙂",
        completed: "ok",
        ignoredStage: "SMILE",
      }),
      "utf8"
    );
    await fs.writeFile(path.join(dir, "persona.local.md"), "local voice only\n", "utf8");

    const profile = loadLocalProfile(dir);

    assert.equal(profile.aliases.length, 3);
    assert.equal(profile.replyPhrases.completionPrefix, "Done:");
    assert.equal(profile.replyPhrases.ignoredKey, undefined);
    assert.equal(profile.reactions.received, "SMILE");
    assert.equal(profile.reactions.completed, "OK");
    assert.equal(profile.reactions.ignoredStage, undefined);
    assert.equal(profile.personaText, "local voice only");
    assert.deepEqual(profile.loadedFiles, [
      "aliases.local.json",
      "reply-phrases.local.json",
      "reactions.local.json",
      "persona.local.md",
    ]);
  });
});

test("applyLocalAliases replaces longer local aliases first", () => {
  const profile = {
    ...emptyLocalProfile(),
    aliases: [
      { from: "US", to: "United States", caseSensitive: true, match: "word" },
      { from: "JE-1000F US", to: "JE-1000F_US", caseSensitive: false, match: "literal" },
    ],
  };

  assert.equal(applyLocalAliases("查 JE-1000F US 草稿包", profile), "查 JE-1000F_US 草稿包");
});

test("localReplyPhrase and localReactionEmojiType fall back cleanly", () => {
  assert.equal(localReplyPhrase({ replyPhrases: { completionPrefix: "Done:" } }, "completionPrefix", "done:"), "Done:");
  assert.equal(localReplyPhrase({ replyPhrases: {} }, "completionPrefix", "done:"), "done:");
  assert.equal(localReactionEmojiType({ reactions: { received: "smile" } }, "received"), "SMILE");
  assert.equal(localReactionEmojiType({ reactions: { received: "GET" } }, "received"), "Get");
  assert.equal(localReactionEmojiType({ reactions: {} }, "received"), "");
});

test("normalizeFeishuEmojiType accepts unicode and canonical names", () => {
  assert.equal(normalizeFeishuEmojiType("🙂"), "SMILE");
  assert.equal(normalizeFeishuEmojiType("ok"), "OK");
  assert.equal(normalizeFeishuEmojiType("GET"), "Get");
  assert.equal(normalizeFeishuEmojiType("custom_type"), "CUSTOM_TYPE");
});
